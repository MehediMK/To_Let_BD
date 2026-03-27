"""
Management command to process cached analytics data and save to database
"""
from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta, date
from properties.models import PropertyAnalytics, PropertyVisit
from properties.signals import process_cached_visits
import json


class Command(BaseCommand):
    help = 'Process cached analytics data (visits, views) and save to database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Process specific date (YYYY-MM-DD). Default: yesterday'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Process all pending dates in cache'
        )

    def handle(self, *args, **options):
        target_date = options.get('date')
        process_all = options.get('all', False)

        if process_all:
            # Process all recent dates
            total_processed = 0
            for days_back in range(1, 8):  # Last 7 days
                check_date = (timezone.now() - timedelta(days=days_back)).strftime("%Y%m%d")
                cache_key = f'property_visit_queue:{check_date}'
                count = cache.llen(cache_key)
                if count > 0:
                    self.stdout.write(f"Processing {count} visits from {check_date}...")
                    processed = process_cached_visits_for_date(check_date)
                    total_processed += processed
                    self.stdout.write(self.style.SUCCESS(f"  ✓ Processed {processed} visits"))
                else:
                    self.stdout.write(f"No pending visits for {check_date}")
            self.stdout.write(self.style.SUCCESS(f"\nTotal processed: {total_processed} visits"))
        else:
            # Process specific date or yesterday
            if not target_date:
                target_date = (timezone.now() - timedelta(days=1)).strftime("%Y%m%d")

            cache_key = f'property_visit_queue:{target_date}'
            count = cache.llen(cache_key)

            if count == 0:
                self.stdout.write(self.style.WARNING(f"No pending visits for {target_date}"))
            else:
                self.stdout.write(f"Processing {count} visits from {target_date}...")
                processed = process_cached_visits_for_date(target_date)
                self.stdout.write(self.style.SUCCESS(f"✓ Processed {processed} visits"))


def process_cached_visits_for_date(date_str):
    """Process visits for a specific cache key date"""
    from django.core.cache import cache
    from django.utils import timezone
    import json

    cache_key = f'property_visit_queue:{date_str}'
    visit_data_list = cache.lrange(cache_key, 0, -1)

    if not visit_data_list:
        return 0

    # Group by property
    visits_to_create = []
    property_date_counts = {}  # (property_id, date) -> {views, unique_visitors}

    for visit_data_str in visit_data_list:
        try:
            visit_data = json.loads(visit_data_str)
            property_id = visit_data['property_id']
            timestamp = timezone.datetime.fromisoformat(visit_data['timestamp'])
            visit_date = timestamp.date()

            key = (property_id, visit_date)
            if key not in property_date_counts:
                property_date_counts[key] = {
                    'views': 0,
                    'unique_visitors_set': set(),
                }

            property_date_counts[key]['views'] += 1

            # Track unique visitor
            user_id = visit_data.get('user_id')
            ip = visit_data.get('ip_address', '')
            if user_id:
                property_date_counts[key]['unique_visitors_set'].add(f"user:{user_id}")
            elif ip:
                property_date_counts[key]['unique_visitors_set'].add(f"ip:{ip}")

            # Create PropertyVisit instance
            visit = PropertyVisit(
                property_id=property_id,
                ip_address=visit_data.get('ip_address', ''),
                user_agent=visit_data.get('user_agent', '')[:500],
                referrer=visit_data.get('referrer', '')[:500],
                user_id=visit_data.get('user_id'),
                session_key=visit_data.get('session_key', ''),
                created_at=timestamp,
            )
            visits_to_create.append(visit)

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Failed to parse visit data: {e}")
            continue

    # Bulk create PropertyVisit records
    batch_size = 1000
    for i in range(0, len(visits_to_create), batch_size):
        batch = visits_to_create[i:i+batch_size]
        PropertyVisit.objects.bulk_create(batch, ignore_conflicts=True)

    # Update PropertyAnalytics
    from django.db import transaction
    with transaction.atomic():
        for (property_id, visit_date), counts in property_date_counts.items():
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
            analytics.views += counts['views']
            analytics.unique_visitors += len(counts['unique_visitors_set'])
            analytics.save(update_fields=['views', 'unique_visitors'])

    # Clear cache
    cache.delete(cache_key)

    return len(visits_to_create)