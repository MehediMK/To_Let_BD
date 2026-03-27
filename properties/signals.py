from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from datetime import date
from .models import UserProfile, Review, Inquiry, Notification, Favorite, Message, PropertyAnalytics, PropertyVisit, Property
from .email_utils import send_inquiry_notification, send_inquiry_confirmation, send_review_notification, send_message_notification
from .geocoding import geocode_address

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    # Ensure profile exists for existing users (e.g., superuser)
    try:
        instance.profile.save()
    except UserProfile.DoesNotExist:
        UserProfile.objects.create(user=instance)


def update_property_rating(review_instance):
    """Update property's average rating and review count"""
    property_obj = review_instance.property
    # Count all reviews, not just verified ones
    reviews = property_obj.reviews.all()
    count = reviews.count()
    if count > 0:
        total = sum(r.rating for r in reviews)
        property_obj.rating = total / count
        property_obj.review_count = count
    else:
        property_obj.rating = 0.0
        property_obj.review_count = 0
    property_obj.save(update_fields=['rating', 'review_count'])


@receiver(post_save, sender=Review)
def review_post_save(sender, instance, created, **kwargs):
    """When a review is added or updated, recalculate property rating"""
    update_property_rating(instance)


@receiver(post_delete, sender=Review)
def review_post_delete(sender, instance, **kwargs):
    """When a review is deleted, recalculate property rating"""
    update_property_rating(instance)


@receiver(post_save, sender=Inquiry)
def inquiry_post_save(sender, instance, created, **kwargs):
    """When a new inquiry is created, notify the property owner and send emails"""
    if created and instance.property and instance.property.owner:
        # Build URLs
        site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
        owner_inquiries_url = f"{site_url}{reverse('owner_inquiries')}"
        my_inquiries_url = f"{site_url}{reverse('my_inquiries')}"

        # Create in-app notification
        Notification.objects.create(
            user=instance.property.owner,
            notification_type='inquiry',
            title=f'New Inquiry for {instance.property.title}',
            message=f'You have a new inquiry from {instance.name} regarding "{instance.property.title}". Message: {instance.message[:100]}{"..." if len(instance.message) > 100 else ""}',
            related_property=instance.property
        )
        # Send email to property owner
        send_inquiry_notification(instance, instance.property, extra_context={
            'site_url': site_url,
            'owner_inquiries_url': owner_inquiries_url,
        })
        # Send confirmation email to inquirer
        send_inquiry_confirmation(instance, instance.property, extra_context={
            'site_url': site_url,
            'my_inquiries_url': my_inquiries_url,
        })


@receiver(post_save, sender=Review)
def review_notification(sender, instance, created, **kwargs):
    """When a new review is created, notify the property owner and send email"""
    if created and instance.property and instance.property.owner:
        site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
        property_url = f"{site_url}{reverse('property_detail', args=[instance.property.pk])}#reviews"

        # Create in-app notification
        Notification.objects.create(
            user=instance.property.owner,
            notification_type='review',
            title=f'New Review for {instance.property.title}',
            message=f'Your property received a new {instance.rating}-star review from {instance.user.username}.',
            related_property=instance.property
        )
        # Send email notification
        send_review_notification(instance, instance.property, extra_context={
            'site_url': site_url,
            'property_url': property_url,
            'property': instance.property,
            'review': instance,
        })


@receiver(post_save, sender=Favorite)
def favorite_notification(sender, instance, created, **kwargs):
    """When a property is favorited, notify the owner"""
    if created and instance.property and instance.property.owner and instance.property.owner != instance.user:
        Notification.objects.create(
            user=instance.property.owner,
            notification_type='favorite',
            title=f'Property Favorited',
            message=f'{instance.user.username} favorited your property "{instance.property.title}".',
            related_property=instance.property
        )


@receiver(post_save, sender=Message)
def message_notification(sender, instance, created, **kwargs):
    """When a message is sent, create a notification for the receiver and send email"""
    if created:
        site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
        inbox_url = f"{site_url}{reverse('inbox')}"

        # Create notification for receiver
        Notification.objects.create(
            user=instance.receiver,
            notification_type='message',
            title=f'New Message from {instance.sender.username}',
            message=f'Subject: {instance.subject}\n\n{instance.body[:100]}{"..." if len(instance.body) > 100 else ""}',
            related_property=instance.related_property
        )
        # Send email notification to receiver
        send_message_notification(instance, instance.receiver, extra_context={
            'site_url': site_url,
            'inbox_url': inbox_url,
        })


# =====================================================
# ANALYTICS SIGNALS
# =====================================================

def process_cached_visits():
    """Process cached PropertyVisit data and save to database in batches"""
    from django.core.cache import cache
    from django.utils import timezone
    from datetime import timedelta
    import json

    # Process yesterday's data (to ensure we have complete day)
    target_date = (timezone.now() - timedelta(days=1)).strftime("%Y%m%d")
    cache_key = f'property_visit_queue:{target_date}'

    # Get all visits from cache
    visit_data_list = cache.lrange(cache_key, 0, -1)
    if not visit_data_list:
        return 0

    # Group by property and date for efficient bulk creation
    visits_to_create = []
    property_date_counts = {}  # (property_id, date) -> {unique_visitors, views}

    for visit_data_str in visit_data_list:
        try:
            visit_data = json.loads(visit_data_str)
            property_id = visit_data['property_id']
            timestamp = timezone.datetime.fromisoformat(visit_data['timestamp'])
            visit_date = timestamp.date()

            # Count views per property per day
            key = (property_id, visit_date)
            if key not in property_date_counts:
                property_date_counts[key] = {
                    'views': 0,
                    'unique_visitors_set': set(),
                    'saves': 0,
                    'inquiries': 0,
                }

            property_date_counts[key]['views'] += 1

            # Track unique visitors
            user_id = visit_data.get('user_id')
            ip = visit_data.get('ip_address', '')
            if user_id:
                property_date_counts[key]['unique_visitors_set'].add(f"user:{user_id}")
            elif ip:
                property_date_counts[key]['unique_visitors_set'].add(f"ip:{ip}")

            # Create PropertyVisit instance (for detailed tracking)
            visit = PropertyVisit(
                property_id=property_id,
                ip_address=visit_data.get('ip_address', ''),
                user_agent=visit_data.get('user_agent', ''),
                referrer=visit_data.get('referrer', ''),
                user_id=visit_data.get('user_id'),
                session_key=visit_data.get('session_key', ''),
                created_at=timestamp,
            )
            visits_to_create.append(visit)

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Failed to parse visit data: {e}")
            continue

    # Bulk create PropertyVisit records (in batches)
    batch_size = 1000
    for i in range(0, len(visits_to_create), batch_size):
        batch = visits_to_create[i:i+batch_size]
        PropertyVisit.objects.bulk_create(batch, ignore_conflicts=True)

    # Update PropertyAnalytics
    from django.db import transaction
    with transaction.atomic():
        for (property_id, visit_date), counts in property_date_counts.items():
            # Get or create analytics record
            analytics, created = PropertyAnalytics.objects.get_or_create(
                property_id=property_id,
                date=visit_date,
                defaults={
                    'views': 0,
                    'saves': 0,
                    'inquiries': 0,
                    'unique_visitors': 0,
                }
            )

            # Update counts
            analytics.views += counts['views']
            analytics.unique_visitors += len(counts['unique_visitors_set'])
            analytics.save(update_fields=['views', 'unique_visitors'])

    # Clear processed data from cache
    cache.delete(cache_key)

    return len(visits_to_create)


@receiver(post_save, sender=Favorite)
def update_favorite_analytics(sender, instance, created, **kwargs):
    """Update daily analytics when a property is favorited"""
    if created:
        today = date.today()
        analytics, created = PropertyAnalytics.objects.get_or_create(
            property=instance.property,
            date=today,
            defaults={
                'unique_visitors': 0,
                'views': 0,
                'saves': 0,
                'inquiries': 0,
            }
        )
        analytics.saves += 1
        analytics.save()


@receiver(post_save, sender=Inquiry)
def update_inquiry_analytics(sender, instance, created, **kwargs):
    """Update daily analytics when an inquiry is submitted"""
    if created:
        today = date.today()
        analytics, created = PropertyAnalytics.objects.get_or_create(
            property=instance.property,
            date=today,
            defaults={
                'unique_visitors': 0,
                'views': 0,
                'saves': 0,
                'inquiries': 0,
            }
        )
        analytics.inquiries += 1
        analytics.save()


def create_missing_analytics():
    """Create analytics entries for properties that don't have today's entry"""
    from django.utils import timezone
    today = date.today()

    # Get all active properties
    properties = Property.objects.filter(is_available=True)

    for prop in properties:
        PropertyAnalytics.objects.get_or_create(
            property=prop,
            date=today,
            defaults={
                'unique_visitors': 0,
                'views': 0,
                'saves': 0,
                'inquiries': 0,
            }
        )


@receiver(post_save, sender=Property)
def auto_geocode_property(sender, instance, created, **kwargs):
    """
    Automatically geocode property when saved if coordinates are missing
    """
    # Skip if coordinates already exist or property has no address
    if instance.latitude and instance.longitude:
        return

    if not instance.address and not instance.location:
        return

    # Only attempt geocoding if we have at least location
    address = instance.address or ""
    city = instance.city or instance.location or ""
    country = instance.country or "Bangladesh"

    try:
        result = geocode_address(
            address=address,
            city=city,
            country=country
        )

        if result:
            # Update property with coordinates (avoid infinite loop by using update)
            Property.objects.filter(pk=instance.pk).update(
                latitude=result['lat'],
                longitude=result['lon']
            )
            print(f"Geocoded property '{instance.title}': {result['lat']}, {result['lon']}")
    except Exception as e:
        # Log but don't prevent save
        print(f"Geocoding failed for property '{instance.title}': {e}")
