"""
Email verification utilities for Rent&Stay
"""
import uuid
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.urls import reverse


def generate_verification_token():
    """Generate a unique verification token"""
    return str(uuid.uuid4())


def set_verification_token(user_profile, token=None):
    """Set verification token for user profile"""
    if token is None:
        token = generate_verification_token()
    user_profile.email_verification_token = token
    user_profile.token_created_at = timezone.now()
    user_profile.save()
    return token


def is_token_valid(user_profile, max_hours=24):
    """Check if verification token is still valid"""
    if not user_profile.token_created_at:
        return False

    expiry_time = user_profile.token_created_at + timedelta(hours=max_hours)
    return timezone.now() < expiry_time


def send_verification_email(request, user_profile):
    """
    Send verification email to user

    Args:
        request: HTTP request object
        user_profile: UserProfile instance
    """
    user = user_profile.user

    # Generate token
    token = set_verification_token(user_profile)

    # Build verification URL
    verify_url = request.build_absolute_uri(
        reverse('verify_email', kwargs={'token': token})
    )

    # Prepare email context
    context = {
        'user': user,
        'verify_url': verify_url,
        'expiry_hours': 24,
    }

    # Render email templates
    subject = 'Verify your email address - Rent&Stay'
    html_message = render_to_string('emails/verify_email.html', context)
    plain_message = render_to_string('emails/verify_email.txt', context)

    # Send email
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@rentstay.com'),
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )

    return True


def verify_email_token(token):
    """
    Verify email token and return user if successful

    Returns:
        User object if verified, None otherwise
    """
    from .models import UserProfile

    try:
        profile = UserProfile.objects.get(email_verification_token=token)
    except UserProfile.DoesNotExist:
        return None

    if is_token_valid(profile):
        profile.email_verified = True
        profile.email_verification_token = None
        profile.token_created_at = None
        profile.save()
        return profile.user
    return None
