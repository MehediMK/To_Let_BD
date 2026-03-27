from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.html import format_html
from .validators import validate_image_size, compress_image

class Agent(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    photo = models.ImageField(upload_to='agents/', blank=True, null=True)
    bio = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Amenity(models.Model):
    """Amenities that properties can have"""
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, blank=True, help_text="FontAwesome icon class")
    category = models.CharField(max_length=50, choices=(
        ('basic', 'Basic'),
        ('comfort', 'Comfort'),
        ('safety', 'Safety'),
        ('entertainment', 'Entertainment'),
        ('utilities', 'Utilities'),
    ), default='comfort')

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

class PropertyImage(models.Model):
    """Additional images for properties (gallery)"""
    property = models.ForeignKey('Property', on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='property_gallery/', validators=[validate_image_size])
    caption = models.CharField(max_length=200, blank=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']
        unique_together = ['property', 'order']

    def __str__(self):
        return f"{self.property.title} - Image {self.order}"

class Inquiry(models.Model):
    """Contact/inquiry from potential tenant"""
    STATUS_CHOICES = (
        ('new', 'New'),
        ('viewed', 'Viewed'),
        ('responded', 'Responded'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('rented', 'Rented'),
    )

    property = models.ForeignKey('Property', on_delete=models.CASCADE, related_name='inquiries')
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    message = models.TextField()
    move_in_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    def __str__(self):
        return f"Inquiry for {self.property.title} by {self.name}"

    class Meta:
        ordering = ['-created_at']

class UserProfile(models.Model):
    """Extended user profile"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=15, blank=True, help_text="Primary contact number")
    bio = models.TextField(blank=True, max_length=500)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, validators=[validate_image_size])
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.CharField(max_length=300, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default='USA')
    is_landlord = models.BooleanField(default=False, help_text="Mark user as property owner/landlord")
    is_tenant = models.BooleanField(default=True, help_text="Mark user as tenant/renter")
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=100, blank=True, null=True, unique=True)
    token_created_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Role-based permissions
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('agent', 'Agent'),
        ('landlord', 'Landlord'),
        ('tenant', 'Tenant'),
        ('staff', 'Staff'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='tenant', help_text="Primary user role")
    assigned_agency = models.ForeignKey('Agency', on_delete=models.SET_NULL, null=True, blank=True, related_name='staff_members', help_text="Agency this user belongs to")

    # Verification
    is_verified_landlord = models.BooleanField(default=False, help_text="Verified landlord badge")
    is_verified_tenant = models.BooleanField(default=False, help_text="Verified tenant badge")
    verification_submitted_at = models.DateTimeField(null=True, blank=True)
    verification_approved_at = models.DateTimeField(null=True, blank=True)
    verification_notes = models.TextField(blank=True, help_text="Verification notes")

    # Preferences
    receive_newsletter = models.BooleanField(default=True)
    receive_marketing = models.BooleanField(default=False)
    receive_sms_notifications = models.BooleanField(default=True)
    receive_email_notifications = models.BooleanField(default=True)
    push_notifications_enabled = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def get_role_display(self):
        return dict(self.ROLE_CHOICES).get(self.role, self.role)

    def is_agency_staff(self):
        return self.assigned_agency is not None

    def can_manage_properties(self):
        return self.role in ['admin', 'agent', 'landlord'] or self.assigned_agency is not None

    def get_verification_badges(self):
        badges = []
        if self.is_verified_landlord:
            badges.append('Verified Landlord')
        if self.is_verified_tenant:
            badges.append('Verified Tenant')
        if self.assigned_agency:
            badges.append(f'Agency: {self.assigned_agency.name}')
        return badges

class Favorite(models.Model):
    """User saved/favorite properties"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorites')
    property = models.ForeignKey('Property', on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'property']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} favorited {self.property.title}"

class PropertyAmenity(models.Model):
    """Through model for Property-Amenity many-to-many"""
    property = models.ForeignKey('Property', on_delete=models.CASCADE, related_name='property_amenities')
    amenity = models.ForeignKey(Amenity, on_delete=models.CASCADE)
    notes = models.CharField(max_length=200, blank=True, help_text="Additional notes about this amenity")
    order = models.IntegerField(default=0, help_text="Order for displaying amenities")

    class Meta:
        unique_together = ['property', 'amenity']
        verbose_name_plural = "Property Amenities"
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.property.title} - {self.amenity.name}"

class Review(models.Model):
    """User reviews for properties"""
    property = models.ForeignKey('Property', on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5 stars"
    )
    comment = models.TextField(max_length=1000, help_text="Your experience with this property")
    is_verified = models.BooleanField(default=False, help_text="Verified if user contacted/rented the property")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    owner_response = models.TextField(blank=True, help_text="Property owner's response to this review")
    owner_response_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['property', 'user']  # One review per user per property

    def __str__(self):
        return f"Review for {self.property.title} by {self.user.username}"

class Notification(models.Model):
    """User notifications for various events"""
    TYPE_CHOICES = (
        ('inquiry', 'New Inquiry'),
        ('review', 'New Review'),
        ('message', 'New Message'),
        ('favorite', 'Property Favorited'),
        ('system', 'System Notification'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    related_property = models.ForeignKey('Property', on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', 'created_at']),
        ]

    def __str__(self):
        return f"{self.notification_type} for {self.user.username}: {self.title}"

    def mark_as_read(self):
        self.is_read = True
        self.save(update_fields=['is_read'])

    def mark_as_unread(self):
        self.is_read = False
        self.save(update_fields=['is_read'])

class Message(models.Model):
    """Private messages between users"""
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_messages')
    related_property = models.ForeignKey('Property', on_delete=models.SET_NULL, null=True, blank=True, related_name='messages')
    subject = models.CharField(max_length=200)
    body = models.TextField()
    parent_message = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies')
    is_read = models.BooleanField(default=False)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-sent_at']
        indexes = [
            models.Index(fields=['receiver', 'is_read', 'sent_at']),
            models.Index(fields=['sender', 'sent_at']),
        ]

    def __str__(self):
        return f"Message from {self.sender} to {self.receiver}: {self.subject}"

    def mark_as_read(self):
        self.is_read = True
        self.save(update_fields=['is_read'])

    def mark_as_unread(self):
        self.is_read = False
        self.save(update_fields=['is_read'])

    @property
    def is_reply(self):
        return self.parent_message is not None

class Property(models.Model):
    PROPERTY_TYPES = (
        ('apartment', 'Apartment'),
        ('house', 'House'),
        ('bungalow', 'Bungalow'),
        ('duplex', 'Duplex'),
        ('floor', 'Whole Floor'),
        ('room', 'Single Room'),
        ('bachelor_room', 'Bachelor Room'),
        ('shared_room', 'Shared Room'),
        ('shop', 'Shop/Commercial'),
        ('office', 'Office Space'),
        ('warehouse', 'Warehouse'),
        ('studio', 'Studio'),
        ('penthouse', 'Penthouse'),
    )

    STATUS_CHOICES = (
        ('available', 'Available'),
        ('rented', 'Rented'),
    )

    FEATURED_CHOICES = (
        ('featured', 'Featured'),
        ('premium', 'Premium'),
        ('new', 'New'),
        ('popular', 'Popular'),
        ('beachfront', 'Beachfront'),
        ('', 'None'),
    )

    YES_NO_CHOICES = (
        ('yes', 'Yes'),
        ('no', 'No'),
        ('allowed', 'Allowed'),
        ('not_allowed', 'Not Allowed'),
    )

    title = models.CharField(max_length=200)
    description = models.TextField()
    property_type = models.CharField(max_length=50, choices=PROPERTY_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    featured_tag = models.CharField(max_length=50, choices=FEATURED_CHOICES, blank=True, default='')
    price = models.DecimalField(max_digits=12, decimal_places=2)  # Increased for BDT
    location = models.CharField(max_length=200, help_text="Area/Neighborhood (e.g., Banani, Gulshan, Dhanmondi)")
    address = models.CharField(max_length=300, blank=True)
    # Bangladesh-specific address fields
    division = models.CharField(max_length=100, blank=True, choices=(
        ('dhaka', 'Dhaka'),
        ('chittagong', 'Chittagong'),
        ('khulna', 'Khulna'),
        ('rajshahi', 'Rajshahi'),
        ('sylhet', 'Sylhet'),
        ('barisal', 'Barisal'),
        ('rangpur', 'Rangpur'),
        ('mymensingh', 'Mymensingh'),
    ))
    district = models.CharField(max_length=100, blank=True, help_text="District (e.g., Dhaka, Chittagong)")
    thana = models.CharField(max_length=100, blank=True, help_text="Thana/Police Station (e.g., Banani, Kotwali)")
    postcode = models.CharField(max_length=10, blank=True, help_text="Postal code")
    city = models.CharField(max_length=100, blank=True, default='Dhaka')
    state = models.CharField(max_length=100, blank=True, default='Dhaka')
    country = models.CharField(max_length=100, default='Bangladesh', blank=True)
    bedrooms = models.IntegerField()
    bathrooms = models.DecimalField(max_digits=3, decimal_places=1)
    square_feet = models.IntegerField()
    main_image = models.ImageField(upload_to='properties/', validators=[validate_image_size])
    gallery_images = models.JSONField(default=list, blank=True)  # Legacy field, will use PropertyImage model
    agent = models.ForeignKey(Agent, on_delete=models.SET_NULL, null=True, blank=True, related_name='properties')
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='owned_properties')
    amenities = models.ManyToManyField('Amenity', through='PropertyAmenity', blank=True, related_name='properties')
    property_rules = models.JSONField(default=dict, blank=True, help_text="Property rules like pets, smoking, parties, etc.")
    availabilities = models.JSONField(default=dict, blank=True, help_text="Availability calendar")
    is_featured = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Additional fields
    year_built = models.IntegerField(null=True, blank=True)
    parking_spaces = models.IntegerField(null=True, blank=True, default=0)
    pets_allowed = models.CharField(max_length=20, choices=YES_NO_CHOICES, blank=True, default='no')
    smoking_allowed = models.CharField(max_length=20, choices=YES_NO_CHOICES, blank=True, default='no')
    parties_allowed = models.CharField(max_length=20, choices=YES_NO_CHOICES, blank=True, default='no')
    quiet_hours = models.CharField(max_length=100, blank=True, help_text="e.g., 10 PM - 7 AM")
    lease_term = models.CharField(max_length=100, blank=True, help_text="e.g., 12 months, month-to-month")
    security_deposit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Security deposit amount")
    application_fee = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="Application fee")
    virtual_tour_url = models.URLField(blank=True, help_text="YouTube/Vimeo/3D tour URL")
    floor_plan_image = models.ImageField(upload_to='floor_plans/', blank=True, null=True, validators=[validate_image_size])
    virtual_tour_360 = models.ImageField(upload_to='virtual_tours_360/', blank=True, null=True, validators=[validate_image_size], help_text="360° panoramic image for immersive virtual tour")
    rating = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(5.0)])
    review_count = models.IntegerField(default=0)
    views = models.PositiveIntegerField(default=0, help_text="Number of times property has been viewed")

    def __str__(self):
        return self.title

    class Meta:
        indexes = [
            models.Index(fields=['is_available', 'property_type']),
            models.Index(fields=['is_available', 'price']),
            models.Index(fields=['is_available', 'location']),
            models.Index(fields=['is_available', 'bedrooms']),
            models.Index(fields=['is_available', 'bathrooms']),
            models.Index(fields=['is_featured', '-created_at']),
            models.Index(fields=['rating', '-review_count']),
        ]

    def get_featured_tag_color(self):
        colors = {
            'featured': 'bg-blue-600',
            'premium': 'bg-green-600',
            'new': 'bg-orange-600',
            'popular': 'bg-purple-600',
            'beachfront': 'bg-teal-600',
        }
        return colors.get(self.featured_tag, 'bg-gray-600')

    def get_amenities_list(self):
        """Return list of amenities as strings"""
        return [pa.amenity.name for pa in self.property_amenities.select_related('amenity').all()]

    def get_amenities_by_category(self):
        """Return amenities grouped by category with icons"""
        from collections import OrderedDict
        categories = OrderedDict()

        # Get category display mapping
        category_choices = dict(Amenity._meta.get_field('category').choices)

        for pa in self.property_amenities.select_related('amenity').order_by('amenity__category', 'order'):
            amenity = pa.amenity
            category = amenity.category
            category_display = category_choices.get(category, category.title())

            if category_display not in categories:
                categories[category_display] = {
                    'code': category,
                    'amenities': [],
                }

            categories[category_display]['amenities'].append({
                'name': amenity.name,
                'icon': amenity.icon,
                'notes': pa.notes,
            })

        return categories

    def get_available_dates(self):
        """Parse availability calendar"""
        if not self.availabilities:
            return []
        # Simple implementation - you can enhance this
        return self.availabilities.get('dates', [])

    def get_price_per_sqft(self):
        """Calculate price per square foot"""
        if self.square_feet and self.square_feet > 0:
            return round(float(self.price) / self.square_feet, 2)
        return 0

    def get_video_embed_html(self, width=640, height=360):
        """
        Returns embed HTML for YouTube/Vimeo URLs.
        Usage: {{ property.get_video_embed_html|safe }}
        """
        if not self.virtual_tour_url:
            return ''

        import re
        youtube_regex = r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})'
        vimeo_regex = r'vimeo\.com\/(\d+)'

        youtube_match = re.search(youtube_regex, self.virtual_tour_url)
        if youtube_match:
            video_id = youtube_match.group(1)
            return format_html(
                '<iframe width="{}" height="{}" src="https://www.youtube.com/embed/{}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen style="border-radius: 8px; max-width: 100%;"></iframe>',
                width, height, video_id
            )

        vimeo_match = re.search(vimeo_regex, self.virtual_tour_url)
        if vimeo_match:
            video_id = vimeo_match.group(1)
            return format_html(
                '<iframe width="{}" height="{}" src="https://player.vimeo.com/video/{}" frameborder="0" allow="autoplay; fullscreen; picture-in-picture" allowfullscreen style="border-radius: 8px; max-width: 100%;"></iframe>',
                width, height, video_id
            )

        # If it's an embed URL already, return as iframe if it looks like one
        if 'iframe' in self.virtual_tour_url or 'embed' in self.virtual_tour_url:
            # Sanitize - we could return as is but be careful
            return format_html(self.virtual_tour_url)

        return ''

# =====================================================
# PAYMENTS & SUBSCRIPTIONS MODELS
# =====================================================

class ListingPackage(models.Model):
    """Package types for property listings (basic, premium, featured)"""
    PACKAGE_TYPES = (
        ('basic', 'Basic'),
        ('premium', 'Premium'),
        ('featured', 'Featured'),
        ('enterprise', 'Enterprise'),
    )

    name = models.CharField(max_length=100)
    package_type = models.CharField(max_length=50, choices=PACKAGE_TYPES, unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.IntegerField(help_text="Package duration in days")
    max_listings = models.IntegerField(help_text="Maximum number of listings allowed")
    allow_featured = models.BooleanField(default=False, help_text="Can feature properties")
    allow_boost = models.BooleanField(default=False, help_text="Can boost properties")
    priority_support = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['price']

    def __str__(self):
        return f"{self.name} (${self.price} - {self.duration_days} days)"

class Subscription(models.Model):
    """User subscriptions to packages"""
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
        ('pending', 'Pending Payment'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscriptions')
    package = models.ForeignKey(ListingPackage, on_delete=models.PROTECT, related_name='subscriptions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    auto_renew = models.BooleanField(default=False)
    stripe_subscription_id = models.CharField(max_length=200, blank=True, help_text="Stripe subscription ID")
    cancelled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.package.name}"

    def is_active(self):
        from django.utils import timezone
        if self.status != 'active':
            return False
        if not self.end_date:
            return False
        return timezone.now() < self.end_date

class Order(models.Model):
    """Purchase orders for packages or featured listings"""
    ORDER_STATUS = (
        ('pending', 'Pending Payment'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    order_number = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='pending')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    stripe_payment_intent_id = models.CharField(max_length=200, blank=True)
    payment_method = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.order_number} - {self.user.username}"

class OrderItem(models.Model):
    """Individual items in an order"""
    ITEM_TYPES = (
        ('package', 'Package Subscription'),
        ('featured', 'Featured Listing'),
        ('boost', 'Property Boost'),
    )

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    item_type = models.CharField(max_length=20, choices=ITEM_TYPES)
    property = models.ForeignKey('Property', on_delete=models.SET_NULL, null=True, blank=True, related_name='order_items')
    package = models.ForeignKey(ListingPackage, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    subscription = models.ForeignKey(Subscription, on_delete=models.SET_NULL, null=True, blank=True, related_name='order_items')

    def __str__(self):
        return f"{self.item_type} - {self.quantity}x ${self.unit_price}"

class Payment(models.Model):
    """Individual payment records"""
    PAYMENT_STATUS = (
        ('pending', 'Pending'),
        ('succeeded', 'Succeeded'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('disputed', 'Disputed'),
    )

    PAYMENT_TYPES = (
        ('subscription', 'Subscription'),
        ('featured', 'Featured Listing'),
        ('boost', 'Property Boost'),
        ('refund', 'Refund'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments')
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS)
    stripe_payment_id = models.CharField(max_length=200, unique=True)
    stripe_charge_id = models.CharField(max_length=200, blank=True)
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.payment_type} - ${self.amount} - {self.status}"

class Commission(models.Model):
    """Commission tracking for agents"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    )

    agent = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='commissions')
    property = models.ForeignKey('Property', on_delete=models.CASCADE, related_name='commissions')
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='commissions')
    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Commission amount")
    percentage = models.FloatField(help_text="Commission percentage (e.g., 5.0 for 5%)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    paid_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Commission for {self.agent.username} - ${self.amount}"

# =====================================================
# PROPERTY MANAGEMENT ADVANCED MODELS
# =====================================================

class PropertyStatusHistory(models.Model):
    """Track property status changes over time"""
    property = models.ForeignKey('Property', on_delete=models.CASCADE, related_name='status_history')
    old_status = models.CharField(max_length=50)
    new_status = models.CharField(max_length=50)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='property_status_changes')
    reason = models.TextField(blank=True, help_text="Reason for status change")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.property.title}: {self.old_status} → {self.new_status}"

class PropertyAnalytics(models.Model):
    """Daily analytics for properties (views, saves, inquiries)"""
    property = models.ForeignKey('Property', on_delete=models.CASCADE, related_name='analytics')
    date = models.DateField()
    views = models.PositiveIntegerField(default=0)
    saves = models.PositiveIntegerField(default=0, help_text="Times added to favorites")
    inquiries = models.PositiveIntegerField(default=0)
    unique_visitors = models.PositiveIntegerField(default=0)
    avg_view_duration = models.FloatField(null=True, blank=True, help_text="Average view duration in seconds")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['property', 'date']
        ordering = ['-date']

    def __str__(self):
        return f"{self.property.title} - {self.date}"

class PropertyComparison(models.Model):
    """User property comparisons"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='property_comparisons')
    properties = models.ManyToManyField('Property', related_name='in_comparisons')
    name = models.CharField(max_length=200, blank=True, help_text="Optional name for comparison")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'name']

    def __str__(self):
        property_count = self.properties.count()
        return f"{self.user.username} - {property_count} properties"

class PropertyRenewalReminder(models.Model):
    """Reminders for property listing renewals"""
    REMINDER_STATUS = (
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('expired', 'Expired'),
    )

    property = models.ForeignKey('Property', on_delete=models.CASCADE, related_name='renewal_reminders')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='renewal_reminders')
    reminder_date = models.DateField(help_text="When to send reminder")
    reminder_days_before = models.IntegerField(help_text="Days before expiry")
    status = models.CharField(max_length=20, choices=REMINDER_STATUS, default='pending')
    email_sent = models.BooleanField(default=False)
    email_sent_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['reminder_date']

    def __str__(self):
        return f"Reminder for {self.property.title} on {self.reminder_date}"

class PropertyHistory(models.Model):
    """Track all changes to property details (audit log)"""
    ACTION_TYPES = (
        ('create', 'Created'),
        ('update', 'Updated'),
        ('status_change', 'Status Changed'),
        ('price_change', 'Price Changed'),
        ('bulk_update', 'Bulk Update'),
    )

    property = models.ForeignKey('Property', on_delete=models.CASCADE, related_name='history')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='property_changes')
    action_type = models.CharField(max_length=50, choices=ACTION_TYPES)
    field_name = models.CharField(max_length=100, blank=True, help_text="Field that was changed")
    old_value = models.TextField(blank=True, help_text="Old value")
    new_value = models.TextField(blank=True, help_text="New value")
    changes = models.JSONField(default=dict, blank=True, help_text="All changed fields and values")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.action_type} on {self.property.title} by {self.user}"

# =====================================================
# USER ROLES & PERMISSIONS MODELS
# =====================================================

class Agency(models.Model):
    """Agency/Team accounts that manage multiple properties"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='agencies/', blank=True, null=True)
    website = models.URLField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField()
    address = models.CharField(max_length=300, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default='USA')
    is_verified = models.BooleanField(default=False)
    subscription = models.ForeignKey(Subscription, on_delete=models.SET_NULL, null=True, blank=True, related_name='agencies')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Agencies"
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_member_count(self):
        return self.members.count()

    def get_property_count(self):
        return self.properties.count()

class AgencyMember(models.Model):
    """Members of an agency with specific roles"""
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('agent', 'Agent'),
        ('staff', 'Staff'),
    )

    agency = models.ForeignKey(Agency, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='agency_memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='agent')
    is_active = models.BooleanField(default=True)
    permissions = models.JSONField(default=dict, blank=True, help_text="Custom permissions JSON")
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['agency', 'user']
        ordering = ['agency', 'role']

    def __str__(self):
        return f"{self.user.username} - {self.agency.name} ({self.role})"

    def can_manage_properties(self):
        return self.role in ['admin', 'manager']

    def can_manage_members(self):
        return self.role in ['admin']

class UserVerification(models.Model):
    """User verification badges"""
    VERIFICATION_TYPES = (
        ('identity', 'Identity Verified'),
        ('landlord', 'Verified Landlord'),
        ('tenant', 'Verified Tenant'),
        ('agency', 'Verified Agency'),
        ('phone', 'Phone Verified'),
        ('email', 'Email Verified'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='verifications')
    verification_type = models.CharField(max_length=50, choices=VERIFICATION_TYPES)
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='verifications_given')
    verification_token = models.CharField(max_length=100, blank=True, unique=True)
    document = models.FileField(upload_to='verifications/', blank=True, null=True, help_text="Supporting document")
    notes = models.TextField(blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'verification_type']
        ordering = ['-created_at']

    def __str__(self):
        status = "✓" if self.is_verified else "✗"
        return f"{self.user.username} - {self.verification_type} {status}"

class UserReport(models.Model):
    """User reports/blocking system"""
    REPORT_REASONS = (
        ('spam', 'Spam'),
        ('inappropriate', 'Inappropriate Content'),
        ('fraud', 'Fraud'),
        ('harassment', 'Harassment'),
        ('other', 'Other'),
    )

    REPORT_STATUS = (
        ('pending', 'Pending Review'),
        ('investigating', 'Under Investigation'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    )

    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reports_made')
    reported_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reports_received')
    reported_property = models.ForeignKey('Property', on_delete=models.SET_NULL, null=True, blank=True, related_name='reports')
    reason = models.CharField(max_length=50, choices=REPORT_REASONS)
    description = models.TextField(help_text="Detailed description of the issue")
    status = models.CharField(max_length=20, choices=REPORT_STATUS, default='pending')
    blocked = models.BooleanField(default=False, help_text="Block interaction between users")
    resolved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reports_resolved')
    resolution_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.reporter.username} reported {self.reported_user.username}"

class AdminApproval(models.Model):
    """Admin approval workflow for listings"""
    property = models.OneToOneField('Property', on_delete=models.CASCADE, related_name='admin_approval')
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='submitted_listings')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_listings')
    status = models.CharField(max_length=20, choices=(
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('changes_requested', 'Changes Requested'),
    ), default='pending')
    review_notes = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.property.title} - {self.status}"

# =====================================================
# SOCIAL & COMMUNITY MODELS
# =====================================================

class NewsletterSubscription(models.Model):
    """Newsletter subscription management"""
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)
    source = models.CharField(max_length=100, default='website', help_text="Where they subscribed")
    preferences = models.JSONField(default=dict, blank=True, help_text="Newsletter preferences")

    class Meta:
        ordering = ['-subscribed_at']

    def __str__(self):
        return self.email

class BlogPost(models.Model):
    """Blog/content section for rental tips, market trends"""
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    )

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='blog_posts')
    content = models.TextField(help_text="Blog post content (HTML from CKEditor)")
    excerpt = models.TextField(max_length=500, blank=True)
    featured_image = models.ImageField(upload_to='blog/', blank=True, null=True)
    category = models.CharField(max_length=100, blank=True)
    tags = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_featured = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    view_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-published_at', '-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('blog_post_detail', kwargs={'slug': self.slug})

class ForumCategory(models.Model):
    """Forum discussion categories"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="FontAwesome icon class")
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = "Forum Categories"

    def __str__(self):
        return self.name

    def get_thread_count(self):
        return self.threads.filter(is_active=True).count()

    def get_post_count(self):
        return Post.objects.filter(thread__category=self, is_active=True).count()

class ForumThread(models.Model):
    """Discussion threads in forum"""
    THREAD_STATUS = (
        ('open', 'Open'),
        ('closed', 'Closed'),
        ('archived', 'Archived'),
    )

    title = models.CharField(max_length=200)
    category = models.ForeignKey(ForumCategory, on_delete=models.CASCADE, related_name='threads')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='forum_threads')
    is_sticky = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=THREAD_STATUS, default='open')
    view_count = models.PositiveIntegerField(default=0)
    last_post_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-is_sticky', '-last_post_at', '-created_at']

    def __str__(self):
        return self.title

    def get_reply_count(self):
        return Post.objects.filter(thread=self, is_active=True).count() - 1  # Exclude original post

    def get_last_post(self):
        return Post.objects.filter(thread=self, is_active=True).order_by('-created_at').first()

class Post(models.Model):
    """Posts within forum threads"""
    thread = models.ForeignKey(ForumThread, on_delete=models.CASCADE, related_name='posts')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='forum_posts')
    content = models.TextField()
    is_edited = models.BooleanField(default=False)
    edited_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='edited_posts')
    edited_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['created_at']
        unique_together = ['thread', 'created_by', 'created_at']  # Prevent duplicate posts

    def __str__(self):
        return f"Post by {self.created_by.username} in {self.thread.title}"

class PostLike(models.Model):
    """Likes on forum posts"""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='post_likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['post', 'user']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} liked {self.post}"

class ReferralProgram(models.Model):
    """Referral program configuration"""
    name = models.CharField(max_length=100)
    description = models.TextField()
    reward_type = models.CharField(max_length=50, choices=(
        ('credit', 'Account Credit'),
        ('discount', 'Discount'),
        ('cash', 'Cash'),
        ('featured', 'Featured Listing'),
    ), default='credit')
    reward_amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Amount of reward")
    reward_percentage = models.FloatField(null=True, blank=True, help_text="Or percentage of referred value")
    max_rewards_per_user = models.IntegerField(default=10, help_text="Max referrals rewarded per user")
    is_active = models.BooleanField(default=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

class UserReferral(models.Model):
    """Track user referrals"""
    referrer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='referrals_made')
    referee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='referrals_received')
    program = models.ForeignKey(ReferralProgram, on_delete=models.SET_NULL, null=True, related_name='referrals')
    referral_code = models.CharField(max_length=50, help_text="Unique referral code used")
    reward_given = models.BooleanField(default=False)
    reward_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    completed_action = models.CharField(max_length=100, default='signup', help_text="Action that triggered reward")
    referred_at = models.DateTimeField(auto_now_add=True)
    reward_given_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-referred_at']
        unique_together = ['referrer', 'referee', 'referral_code']

    def __str__(self):
        return f"{self.referrer.username} referred {self.referee.username}"

class SocialShare(models.Model):
    """Track social shares of properties"""
    SHARE_PLATFORMS = (
        ('facebook', 'Facebook'),
        ('twitter', 'Twitter/X'),
        ('whatsapp', 'WhatsApp'),
        ('linkedin', 'LinkedIn'),
        ('pinterest', 'Pinterest'),
        ('email', 'Email'),
        ('other', 'Other'),
    )

    property = models.ForeignKey('Property', on_delete=models.CASCADE, related_name='social_shares')
    platform = models.CharField(max_length=50, choices=SHARE_PLATFORMS)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='social_shares')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.property.title} shared on {self.platform}"

# =====================================================
# API & MOBILE MODELS
# =====================================================

class APIToken(models.Model):
    """API tokens for mobile app (alternative to JWT refresh tokens)"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='api_tokens')
    token = models.CharField(max_length=64, unique=True)
    device_name = models.CharField(max_length=200, blank=True)
    device_id = models.CharField(max_length=200, blank=True, help_text="Unique device identifier")
    is_active = models.BooleanField(default=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.device_name}"

    def is_valid(self):
        from django.utils import timezone
        if not self.is_active:
            return False
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        return True

class PushNotification(models.Model):
    """Push notifications for mobile app"""
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='push_notifications')
    title = models.CharField(max_length=200)
    body = models.TextField()
    data = models.JSONField(default=dict, blank=True, help_text="Additional data payload")
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal')
    sent_to_firebase = models.BooleanField(default=False)
    firebase_message_id = models.CharField(max_length=200, blank=True)
    clicked = models.BooleanField(default=False)
    clicked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification to {self.user.username}: {self.title}"

class WebhookEndpoint(models.Model):
    """Webhook endpoints for external services"""
    EVENT_TYPES = (
        ('payment.succeeded', 'Payment Succeeded'),
        ('payment.failed', 'Payment Failed'),
        ('subscription.updated', 'Subscription Updated'),
        ('listing.published', 'Listing Published'),
        ('listing.expired', 'Listing Expired'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='webhook_endpoints')
    url = models.URLField(help_text="Webhook URL")
    secret = models.CharField(max_length=100, help_text="Webhook secret for verification")
    events = models.JSONField(default=list, help_text="List of events to subscribe to")
    is_active = models.BooleanField(default=True)
    last_sent_at = models.DateTimeField(null=True, blank=True)
    failure_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Webhook for {self.user.username} - {self.url[:50]}"
