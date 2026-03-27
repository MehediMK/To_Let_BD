"""
Geocoding utilities for Rent&Stay
"""
import requests
from django.conf import settings
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

class GeocodingService:
    """
    Service for geocoding addresses using Nominatim (OpenStreetMap) or other providers
    """
    NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

    def __init__(self):
        self.user_agent = "Rent&Stay Django App (your-email@example.com)"

    def geocode(self, address, city=None, country=None, limit=1):
        """
        Geocode an address to get latitude and longitude

        Args:
            address: Street address
            city: City name
            country: Country name
            limit: Number of results to return

        Returns:
            dict: {'lat': float, 'lon': float, 'display_name': str} or None
        """
        # Build query string
        query_parts = []
        if address:
            query_parts.append(address)
        if city:
            query_parts.append(city)
        if country:
            query_parts.append(country)

        query = ', '.join(query_parts)

        if not query.strip():
            return None

        # Check cache first
        cache_key = f"geocode:{query.lower().strip()}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            params = {
                'q': query,
                'format': 'json',
                'limit': limit,
                'addressdetails': 1,
            }

            headers = {
                'User-Agent': self.user_agent,
            }

            response = requests.get(self.NOMINATIM_URL, params=params, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data:
                    result = {
                        'lat': float(data[0]['lat']),
                        'lon': float(data[0]['lon']),
                        'display_name': data[0]['display_name'],
                        'address': data[0].get('address', {})
                    }
                    # Cache for 30 days
                    cache.set(cache_key, result, 30 * 24 * 3600)
                    return result
            else:
                logger.warning(f"Geocoding failed with status {response.status_code} for query: {query}")

        except Exception as e:
            logger.error(f"Geocoding error for query '{query}': {str(e)}")

        return None

    def reverse_geocode(self, lat, lon):
        """
        Reverse geocode coordinates to get address

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            dict: Address components or None
        """
        cache_key = f"reverse_geocode:{lat},{lon}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            params = {
                'lat': lat,
                'lon': lon,
                'format': 'json',
                'addressdetails': 1,
            }

            headers = {
                'User-Agent': self.user_agent,
            }

            response = requests.get(
                "https://nominatim.openstreetmap.org/reverse",
                params=params,
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                result = {
                    'display_name': data.get('display_name', ''),
                    'address': data.get('address', {})
                }
                cache.set(cache_key, result, 30 * 24 * 3600)
                return result

        except Exception as e:
            logger.error(f"Reverse geocoding error for {lat},{lon}: {str(e)}")

        return None


def geocode_address(address, city=None, country=None):
    """
    Simple function to geocode an address

    Usage:
        result = geocode_address("House 12, Road 5", city="Dhaka", country="Bangladesh")
    """
    service = GeocodingService()
    return service.geocode(address, city, country)