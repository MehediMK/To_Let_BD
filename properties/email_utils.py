"""
Email notification utilities
"""
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings


def send_email_notification(subject, template_name, context, recipient_email, extra_context=None):
    """
    Send an email using a template.

    Args:
        subject: Email subject
        template_name: Name of the template in templates/emails/ (without extension)
        context: Base context for the email
        recipient_email: Email address of recipient
        extra_context: Additional context that takes precedence

    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        # Merge extra_context if provided
        if extra_context:
            context.update(extra_context)

        # Add site URL to context if not already present
        if 'site_url' not in context:
            if settings.DEBUG:
                context['site_url'] = 'http://localhost:8000'
            else:
                context['site_url'] = getattr(settings, 'SITE_URL', 'http://localhost:8000')

        # Render email body from template
        body = render_to_string(f'emails/{template_name}.txt', context)

        # Determine if we should send or just log (console backend)
        if settings.DEBUG and 'console' in settings.EMAIL_BACKEND:
            print(f"\n{'='*60}")
            print(f"EMAIL TO: {recipient_email}")
            print(f"SUBJECT: {subject}")
            print(f"{'='*60}")
            print(body)
            print(f"{'='*60}\n")
            return True

        # Send email
        send_mail(
            subject=subject,
            message=body.strip(),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False


def send_inquiry_notification(inquiry, property_obj, extra_context=None):
    """Send email to the selected recipient (owner or agent) about new inquiry"""
    # Determine recipient: use inquiry.recipient if set, else fallback to property.owner
    recipient = inquiry.recipient or property_obj.owner
    if not recipient or not recipient.email:
        return False

    subject = f'New Inquiry for {property_obj.title}'
    context = {
        'recipient_name': recipient.get_full_name() or recipient.username,
        'property': property_obj,
        'inquiry': inquiry,
    }
    return send_email_notification(subject, 'inquiry_created', context, recipient.email, extra_context)


def send_inquiry_confirmation(inquiry, property_obj, extra_context=None):
    """Send confirmation email to the person who submitted inquiry"""
    subject = f'Your inquiry about {property_obj.title} was received'
    context = {
        'inquirer_name': inquiry.name,
        'property': property_obj,
        'inquiry': inquiry,
    }
    return send_email_notification(subject, 'inquiry_confirmation', context, inquiry.email, extra_context)


def send_review_notification(review, property_obj, extra_context=None):
    """Send email to property owner about new review"""
    owner = property_obj.owner
    if not owner or not owner.email:
        return False

    subject = f'New Review for {property_obj.title}'
    context = {
        'owner_name': owner.get_full_name() or owner.username,
        'property': property_obj,
        'review': review,
    }
    return send_email_notification(subject, 'review_received', context, owner.email, extra_context)


def send_message_notification(message, receiver, extra_context=None):
    """Send email notification about new message"""
    if not receiver.email:
        return False

    subject = f'New Message: {message.subject}'
    context = {
        'receiver_name': receiver.get_full_name() or receiver.username,
        'sender_name': message.sender.get_full_name() or message.sender.username,
        'related_property': message.related_property,
        'subject': message.subject,
        'body': message.body,
    }
    return send_email_notification(subject, 'new_message', context, receiver.email, extra_context)
