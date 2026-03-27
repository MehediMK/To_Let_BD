"""
Management command to initialize analytics for existing properties
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, date
from properties.models import Property, PropertyAnalytics, PropertyVisit


class Command(BaseCommand):
    help = 'Initialize analytics for all properties and create missing daily records'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of past days to initialize (default: 30)'
        )

    def handle(self, *args, **options):
        days = options['days']
        self.stdout.write(self.style.SUCCESS(f'Initializing analytics for {days} days...'))

        # Get all active properties
        properties = Property.objects.filter(is_available=True)
        self.stdout.write(f'Found {properties.count()} active properties')

        created_count = 0
        skipped_count = 0

        for prop in properties:
            for day_offset in range(days):
                target_date = timezone.now().date() - timedelta(days=day_offset)

                # Check if analytics already exists
                exists = PropertyAnalytics.objects.filter(
                    property=prop,
                    date=target_date
                ).exists()

                if not exists:
                    # Create empty analytics record
                    PropertyAnalytics.objects.create(
                        property=prop,
                        date=target_date,
                        views=0,
                        saves=0,
                        inquiries=0,
                        unique_visitors=0
                    )
                    created_count += 1
                else:
                    skipped_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Completed! Created {created_count} analytics records, {skipped_count} already existed.'
            )
        )

        # Show summary of existing analytics
        total_analytics = PropertyAnalytics.objects.count()
        self.stdout.write(f'Total analytics records in database: {total_analytics}')

        # Show total visits tracked
        total_visits = PropertyVisit.objects.count()
        self.stdout.write(f'Total property visits tracked: {total_visits}')