from django.core.management.base import BaseCommand
from properties.models import Amenity

class Command(BaseCommand):
    help = 'Populate database with common amenities'

    def handle(self, *args, **kwargs):
        amenities_data = [
            # Basic
            {'name': 'Air Conditioning', 'icon': 'fa-snowflake', 'category': 'comfort'},
            {'name': 'Heating', 'icon': 'fa-fire', 'category': 'comfort'},
            {'name': 'Washer/Dryer', 'icon': 'fa-soap', 'category': 'utilities'},
            {'name': 'Dishwasher', 'icon': 'fa-soap', 'category': 'utilities'},
            {'name': 'Refrigerator', 'icon': 'fa-snowflake', 'category': 'utilities'},
            {'name': 'Oven/Range', 'icon': 'fa-fire-burner', 'category': 'utilities'},
            {'name': 'Microwave', 'icon': 'fa-radiation', 'category': 'utilities'},
            {'name': 'WiFi', 'icon': 'fa-wifi', 'category': 'utilities'},
            {'name': 'Cable/Satellite TV', 'icon': 'fa-tv', 'category': 'entertainment'},
            {'name': 'Internet', 'icon': 'fa-network-wired', 'category': 'utilities'},

            # Comfort
            {'name': 'Hardwood Floors', 'icon': 'fa-layer-group', 'category': 'comfort'},
            {'name': 'Carpeted Floors', 'icon': 'fa-square', 'category': 'comfort'},
            {'name': 'Balcony/Patio', 'icon': 'fa-door-open', 'category': 'comfort'},
            {'name': 'Fireplace', 'icon': 'fa-fire', 'category': 'comfort'},
            {'name': 'Walk-in Closet', 'icon': 'fa-wardrobe', 'category': 'comfort'},
            {'name': 'Storage Space', 'icon': 'fa-box-archive', 'category': 'comfort'},

            # Safety
            {'name': 'Smoke Detector', 'icon': 'fa-bell-slash', 'category': 'safety'},
            {'name': 'Carbon Monoxide Detector', 'icon': 'fa-bell', 'category': 'safety'},
            {'name': 'Fire Extinguisher', 'icon': 'fa-fire-extinguisher', 'category': 'safety'},
            {'name': 'First Aid Kit', 'icon': 'fa-kit-medical', 'category': 'safety'},
            {'name': 'Secure Entry', 'icon': 'fa-lock', 'category': 'safety'},
            {'name': 'Security System', 'icon': 'fa-shield-halved', 'category': 'safety'},
            {'name': 'Intercom', 'icon': 'fa-phone', 'category': 'safety'},

            # Entertainment
            {'name': 'Smart TV', 'icon': 'fa-tv', 'category': 'entertainment'},
            {'name': 'Home Theater', 'icon': 'fa-film', 'category': 'entertainment'},
            {'name': 'Gaming Console', 'icon': 'fa-gamepad', 'category': 'entertainment'},
            {'name': 'Sound System', 'icon': 'fa-music', 'category': 'entertainment'},

            # Outdoor
            {'name': 'Parking', 'icon': 'fa-car', 'category': 'basic'},
            {'name': 'Garage', 'icon': 'fa-car-side', 'category': 'basic'},
            {'name': 'Gym/Fitness', 'icon': 'fa-dumbbell', 'category': 'comfort'},
            {'name': 'Pool', 'icon': 'fa-person-swimming', 'category': 'comfort'},
            {'name': 'Hot Tub', 'icon': 'fa-hot-tub-person', 'category': 'comfort'},
            {'name': 'Garden/Backyard', 'icon': 'fa-tree', 'category': 'comfort'},
            {'name': 'BBQ/Grill', 'icon': 'fa-fire-burner', 'category': 'comfort'},
            {'name': 'Pet Friendly', 'icon': 'fa-paw', 'category': 'comfort'},
            {'name': 'Laundry Room', 'icon': 'fa-soap', 'category': 'utilities'},

            # Kitchen
            {'name': 'Stainless Appliances', 'icon': 'fa-blender', 'category': 'utilities'},
            {'name': 'Garbage Disposal', 'icon': 'fa-trash', 'category': 'utilities'},
            {'name': 'Breakfast Nook', 'icon': 'fa-coffee', 'category': 'comfort'},
            {'name': 'Island Kitchen', 'icon': 'fa-utensils', 'category': 'comfort'},
        ]

        created_count = 0
        for amenity_data in amenities_data:
            amenity, created = Amenity.objects.get_or_create(
                name=amenity_data['name'],
                defaults={
                    'icon': amenity_data['icon'],
                    'category': amenity_data['category']
                }
            )
            if created:
                created_count += 1
                self.stdout.write(f'Created amenity: {amenity.name}')
            else:
                self.stdout.write(f'Amenity exists: {amenity.name}')

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully populated amenities. Total: {Amenity.objects.count()} (Created: {created_count})'
            )
        )
