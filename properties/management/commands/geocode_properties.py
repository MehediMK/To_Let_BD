"""
Management command to geocode all properties without coordinates
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from properties.models import Property
from properties.geocoding import geocode_address
import time


class Command(BaseCommand):
    help = 'Geocode all properties that are missing latitude/longitude coordinates'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            help='Limit number of properties to process'
        )
        parser.add_argument(
            '--property-id',
            type=int,
            help='Geocode specific property by ID'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force re-geocode even if coordinates exist'
        )

    def handle(self, *args, **options):
        limit = options.get('limit')
        property_id = options.get('property_id')
        force = options.get('force', False)

        if property_id:
            properties = Property.objects.filter(pk=property_id)
        else:
            properties = Property.objects.all()
            if not force:
                properties = properties.filter(latitude__isnull=True, longitude__isnull=True)

        if limit:
            properties = properties[:limit]

        total = properties.count()
        self.stdout.write(f'Processing {total} properties...')

        success_count = 0
        failed_count = 0

        for prop in properties:
            try:
                # Build address components
                address = prop.address or ""
                location = prop.location or ""
                city = prop.city or ""
                country = prop.country or "Bangladesh"

                # Use location as city if city not set
                if not city and location:
                    city = location

                self.stdout.write(f"Geocoding: {prop.title} ({prop.pk})")

                result = geocode_address(
                    address=address,
                    city=city,
                    country=country
                )

                if result:
                    prop.latitude = result['lat']
                    prop.longitude = result['lon']
                    prop.save(update_fields=['latitude', 'longitude'])
                    success_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  ✓ Success: {result['lat']}, {result['lon']}"
                        )
                    )
                else:
                    failed_count += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f"  ✗ No results found for: {address}, {city}, {country}"
                        )
                    )

                # Be nice to the Nominatim API - rate limit to 1 request per second
                time.sleep(1)

            except Exception as e:
                failed_count += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"  ✗ Error: {str(e)}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nCompleted! Success: {success_count}, Failed: {failed_count}"
            )
        )