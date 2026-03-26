"""
Rate limiting utilities for Rent&Stay
"""
import time
from django.core.cache import cache
from django.http import JsonResponse
from functools import wraps


def get_client_ip(request):
    """Extract client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def rate_limit(key_prefix, limit=5, period=300):
    """
    Rate limiting decorator

    Args:
        key_prefix: Prefix for cache key (e.g., 'signup', 'inquiry')
        limit: Number of allowed requests per period
        period: Time period in seconds (default 5 minutes = 300s)

    Usage:
        @rate_limit('signup', limit=5, period=300)
        def my_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            ip = get_client_ip(request)
            if not ip:
                # If we can't get IP, allow but log
                return view_func(request, *args, **kwargs)

            cache_key = f'rate_limit_{key_prefix}:{ip}'
            now = time.time()
            data = cache.get(cache_key, {'count': 0, 'reset_time': now + period})

            # Reset if period has passed
            if now > data['reset_time']:
                data = {'count': 0, 'reset_time': now + period}

            # Check limit
            if data['count'] >= limit:
                return JsonResponse(
                    {'error': 'Rate limit exceeded. Please try again later.'},
                    status=429
                )

            # Increment count
            data['count'] += 1
            cache.set(cache_key, data, period)

            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator


def clear_rate_limit(key_prefix, identifier=None):
    """
    Clear rate limit for a specific key and identifier (usually IP or user identifier)

    Args:
        key_prefix: The same prefix used in decorator
        identifier: IP or user identifier. If None, will clear for all IPs (expensive)
    """
    if identifier:
        cache_key = f'rate_limit_{key_prefix}:{identifier}'
        cache.delete(cache_key)
    else:
        # Clear all keys with this prefix (use cautiously)
        # This requires iterating over cache keys which may be expensive
        pattern = f'rate_limit_{key_prefix}:*'
        # Note: Django cache doesn't support pattern deletion by default
        # You'd need to implement based on your cache backend
        pass
