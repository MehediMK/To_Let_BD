from django.core.management.base import BaseCommand
from properties.models import Property, Agent
from django.core.files import File
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Populate database with sample properties'

    def handle(self, *args, **kwargs):
        # Create agents if they don't exist
        agents_data = [
            {
                'name': 'Sarah Johnson',
                'email': 'sarah.johnson@rentstay.com',
                'phone': '+1-555-0101',
                'bio': 'Experienced real estate agent specializing in urban properties.'
            },
            {
                'name': 'Michael Chen',
                'email': 'michael.chen@rentstay.com',
                'phone': '+1-555-0102',
                'bio': 'Luxury property expert with 10+ years in the market.'
            },
            {
                'name': 'Emily Davis',
                'email': 'emily.davis@rentstay.com',
                'phone': '+1-555-0103',
                'bio': 'Focused on helping first-time renters find their perfect home.'
            },
            {
                'name': 'James Wilson',
                'email': 'james.wilson@rentstay.com',
                'phone': '+1-555-0104',
                'bio': 'Family homes and suburban properties specialist.'
            },
            {
                'name': 'Robert Martinez',
                'email': 'robert.martinez@rentstay.com',
                'phone': '+1-555-0105',
                'bio': 'High-end properties and penthouses in prime locations.'
            },
            {
                'name': 'Lisa Thompson',
                'email': 'lisa.thompson@rentstay.com',
                'phone': '+1-555-0106',
                'bio': 'Beachfront and coastal property expert.'
            }
        ]

        agents = []
        for agent_data in agents_data:
            agent, created = Agent.objects.get_or_create(
                email=agent_data['email'],
                defaults=agent_data
            )
            agents.append(agent)
            if created:
                self.stdout.write(f'Created agent: {agent.name}')
            else:
                self.stdout.write(f'Agent exists: {agent.name}')

        # Sample properties
        properties_data = [
            {
                'title': 'Modern Downtown Loft',
                'description': 'Stunning modern loft in the heart of downtown. Features floor-to-ceiling windows, high-end finishes, and amazing city views. Perfect for professionals seeking an urban lifestyle. Building amenities include 24-hour doorman, fitness center, and rooftop access.',
                'property_type': 'apartment',
                'status': 'available',
                'featured_tag': '',
                'price': 3500,
                'location': '123 Main Street, New York',
                'address': '123 Main Street, New York, NY 10001',
                'bedrooms': 2,
                'bathrooms': 1,
                'square_feet': 1200,
                'agent': agents[0],
                'is_featured': True,
                'is_available': True,
            },
            {
                'title': 'Sunny Suburban House',
                'description': 'Beautiful family home in a quiet suburban neighborhood. Large backyard, modern kitchen, and spacious living areas. Close to schools, parks, and shopping centers. Perfect for families looking for space and comfort.',
                'property_type': 'house',
                'status': 'available',
                'featured_tag': 'premium',
                'price': 4200,
                'location': '456 Oak Avenue, Los Angeles',
                'address': '456 Oak Avenue, Los Angeles, CA 90001',
                'bedrooms': 4,
                'bathrooms': 2.5,
                'square_feet': 2500,
                'agent': agents[1],
                'is_featured': True,
                'is_available': True,
            },
            {
                'title': 'Cozy Studio Loft',
                'description': 'Charming studio in Brooklyn\'s art district. Exposed brick walls, high ceilings, and modern amenities. Walking distance to cafes, galleries, and public transport. Ideal for artists and young professionals.',
                'property_type': 'studio',
                'status': 'available',
                'featured_tag': 'new',
                'price': 1850,
                'location': '789 Art District, Brooklyn',
                'address': '789 Art District, Brooklyn, NY 11201',
                'bedrooms': 0,
                'bathrooms': 1,
                'square_feet': 650,
                'agent': agents[2],
                'is_featured': True,
                'is_available': True,
            },
            {
                'title': 'Family Home with Garden',
                'description': 'Spacious family home featuring a large private garden. Updated throughout with modern finishes while maintaining charm. Excellent school district and safe neighborhood. Garage and driveway parking included.',
                'property_type': 'house',
                'status': 'available',
                'featured_tag': 'popular',
                'price': 3800,
                'location': '321 Maple Drive, Seattle',
                'address': '321 Maple Drive, Seattle, WA 98101',
                'bedrooms': 3,
                'bathrooms': 2,
                'square_feet': 1800,
                'agent': agents[3],
                'is_featured': True,
                'is_available': True,
            },
            {
                'title': 'Luxury Penthouse',
                'description': 'Exceptional penthouse with panoramic ocean and city views. Premium finishes throughout including marble floors, custom kitchen, and smart home system. Private elevator access, concierge service, and resort-style pool.',
                'property_type': 'penthouse',
                'status': 'available',
                'featured_tag': 'featured',
                'price': 8500,
                'location': '555 Sky Tower, Miami',
                'address': '555 Sky Tower, Miami, FL 33139',
                'bedrooms': 3,
                'bathrooms': 3,
                'square_feet': 3200,
                'agent': agents[4],
                'is_featured': True,
                'is_available': True,
            },
            {
                'title': 'Ocean View Villa',
                'description': 'Stunning beachfront villa with direct ocean access. Private beach, infinity pool, and outdoor dining area. Wake up to breathtaking sunrises and enjoy the coastal lifestyle. Fully furnished and ready for immediate move-in.',
                'property_type': 'villa',
                'status': 'available',
                'featured_tag': 'beachfront',
                'price': 5200,
                'location': '888 Coastal Road, San Diego',
                'address': '888 Coastal Road, San Diego, CA 92109',
                'bedrooms': 4,
                'bathrooms': 3,
                'square_feet': 2800,
                'agent': agents[5],
                'is_featured': True,
                'is_available': True,
            }
        ]

        for prop_data in properties_data:
            # Check if property with same title exists
            if not Property.objects.filter(title=prop_data['title']).exists():
                property_obj = Property.objects.create(**prop_data)
                self.stdout.write(f'Created property: {property_obj.title}')
            else:
                self.stdout.write(f'Property exists: {prop_data["title"]}')

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully populated database with {len(properties_data)} properties and {len(agents)} agents'
            )
        )
