"""
Bangladesh-specific template filters
"""
from django import template
from django.utils.html import format_html
from decimal import Decimal

register = template.Library()

@register.filter
def bdt(amount):
    """
    Format a number as Bangladeshi Taka currency.

    Usage: {{ property.price|bdt }}
    Returns: ৳25,000
    """
    if amount is None:
        return '৳0'

    try:
        # Convert to Decimal if it's a string or number
        if isinstance(amount, str):
            amount = Decimal(amount)

        # Format with commas as thousand separators
        # No decimal places for rent prices typically
        formatted = f"{amount:,.0f}"

        # Add BDT symbol
        return format_html('৳{}', formatted)
    except (ValueError, Decimal.InvalidOperation):
        return amount

@register.filter
def bdt_with_decimal(amount):
    """
    Format with 2 decimal places (for security deposits etc.)
    """
    if amount is None:
        return '৳0.00'

    try:
        if isinstance(amount, str):
            amount = Decimal(amount)

        formatted = f"{amount:,.2f}"
        return format_html('৳{}', formatted)
    except (ValueError, Decimal.InvalidOperation):
        return amount

@register.filter
def phone_bd(phone):
    """
    Format Bangladeshi phone number with proper spacing.
    Converts 01712345678 to 01712-345678 or 8801712345678 to +880 1712-345678
    """
    if not phone:
        return phone

    # Remove all non-digit characters except +
    clean = ''.join(c for c in str(phone) if c.isdigit() or c == '+')

    # If starts with 01 (local format)
    if clean.startswith('01') and len(clean) == 11:
        return f"{clean[:5]}-{clean[5:]}"

    # If starts with 880 (international format)
    if clean.startswith('880') and len(clean) == 13:
        return f"+880 {clean[3:7]}-{clean[7:]}"

    return phone

@register.simple_tag
def get_property_type_display(property_type_code, property_types):
    """
    Get display name for property type code.

    Usage: {% get_property_type_display property.property_type property_types as type_display %}
    """
    for code, name in property_types:
        if code == property_type_code:
            return name
    return property_type_code


@register.filter
def intcomma(value):
    """
    Format an integer with commas as thousand separators.

    Usage: {{ value|intcomma }}
    Returns: 1,000,000
    """
    if value is None:
        return ''

    try:
        return f"{int(value):,}"
    except (ValueError, TypeError):
        return value
