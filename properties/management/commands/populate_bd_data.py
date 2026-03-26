"""
Populate Bangladesh-specific data: divisions, districts, amenities, etc.
"""
from django.core.management.base import BaseCommand
from properties.models import Amenity, Property

class Command(BaseCommand):
    help = 'Populate Bangladesh-specific data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Populating Bangladesh-specific data...')

        # Bangladesh Divisions and their major districts/thanas
        # For simplicity, we'll add amenities first

        # Bangladesh-specific amenities
        bd_amenities = [
            # Utilities
            ('Generator', 'bolt', 'utilities'),
            ('24/7 Water Supply', 'tint', 'utilities'),
            ('Gas Supply', 'flame', 'utilities'),
            ('Solar Panel', 'sun', 'utilities'),
            ('Borewell', 'water', 'utilities'),

            # Safety
            ('24/7 Security', 'shield-alt', 'safety'),
            ('CCTV Surveillance', 'video', 'safety'),
            ('Intercom', 'phone', 'safety'),
            ('Fire Extinguisher', 'fire', 'safety'),

            # Comfort
            ('Air Conditioning', 'snowflake', 'comfort'),
            ('Ceiling Fan', 'fan', 'comfort'),
            ('Geyser', 'hot-water', 'comfort'),
            ('Modern Kitchen', 'kitchen', 'comfort'),
            ('Built-in Wardrobe', 'hanger', 'comfort'),
            ('Balcony', 'tree', 'comfort'),
            ('Terrace Access', 'sun', 'comfort'),

            # Basic
            ('Furnished', 'couch', 'basic'),
            ('Semi-Furnished', 'home', 'basic'),
            ('Unfurnished', 'box', 'basic'),
            ('Parking Space', 'parking', 'basic'),
            ('Elevator', 'elevator', 'basic'),
            ('Service Elevator', 'elevator', 'basic'),

            # Entertainment
            ('WiFi Internet', 'wifi', 'entertainment'),
            ('Cable TV', 'tv', 'entertainment'),
            ('Gym', 'dumbbell', 'entertainment'),
            ('Swimming Pool', 'water', 'entertainment'),
            ('Play Area', 'gamepad', 'entertainment'),

            # BD-specific
            ('Rooftop', 'home', 'utilities'),
            ('Servant Quarter', 'user', 'basic'),
            ('Parking for 2+ Cars', 'parking', 'basic'),
            ('Modular Kitchen', 'kitchen', 'comfort'),
            ('French Windows', 'maximize', 'comfort'),
        ]

        created_count = 0
        for name, icon, category in bd_amenities:
            amenity, created = Amenity.objects.get_or_create(
                name=name,
                defaults={'icon': icon, 'category': category}
            )
            if created:
                created_count += 1
                self.stdout.write(f'  ✓ Created amenity: {name}')
            else:
                self.stdout.write(f'  ✓ Amenity exists: {name}')

        self.stdout.write(
            self.style.SUCCESS(f'\nSuccessfully populated amenities! Created {created_count} new amenities.')
        )

        # Optional: Update existing properties with BD-specific tags
        self.stdout.write('\nUpdating existing Property objects...')
        # This can be extended later

        self.stdout.write(
            self.style.SUCCESS('\n✅ Bangladesh data population complete!')
        )
