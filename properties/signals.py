from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.urls import reverse
from django.conf import settings
from .models import UserProfile, Review, Inquiry, Notification, Favorite, Message
from .email_utils import send_inquiry_notification, send_inquiry_confirmation, send_review_notification, send_message_notification

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
