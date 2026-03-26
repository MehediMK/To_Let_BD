from django.contrib import admin
from .models import Property, Agent, Amenity, PropertyImage, Inquiry, UserProfile, Favorite, PropertyAmenity, Review

@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone')
    search_fields = ('name', 'email', 'phone')

@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'icon')
    list_filter = ('category',)
    search_fields = ('name',)

@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
    list_display = ('property', 'order', 'created_at')
    list_filter = ('property',)
    search_fields = ('property__title', 'caption')
    ordering = ('-created_at',)

@admin.register(PropertyAmenity)
class PropertyAmenityAdmin(admin.ModelAdmin):
    list_display = ('property', 'amenity', 'notes')
    list_filter = ('property', 'amenity', 'amenity__category')
    search_fields = ('property__title', 'amenity__name', 'notes')

@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ('property', 'name', 'email', 'status', 'created_at')
    list_filter = ('status', 'created_at', 'property')
    search_fields = ('name', 'email', 'phone', 'property__title', 'message')
    readonly_fields = ('created_at', 'updated_at', 'ip_address')
    list_editable = ('status',)
    actions = ['mark_responded', 'mark_approved', 'mark_rejected']

    def mark_responded(self, request, queryset):
        queryset.update(status='responded')
    mark_responded.short_description = "Mark selected inquiries as responded"

    def mark_approved(self, request, queryset):
        queryset.update(status='approved')
    mark_approved.short_description = "Mark selected inquiries as approved"

    def mark_rejected(self, request, queryset):
        queryset.update(status='rejected')
    mark_rejected.short_description = "Mark selected inquiries as rejected"

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'is_landlord', 'is_tenant', 'email_verified', 'phone_verified')
    list_filter = ('is_landlord', 'is_tenant', 'email_verified', 'phone_verified', 'country')
    search_fields = ('user__username', 'user__email', 'phone', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'property', 'created_at')
    list_filter = ('created_at', 'user')
    search_fields = ('user__username', 'property__title')
    readonly_fields = ('created_at',)

class PropertyAmenityInline(admin.TabularInline):
    model = PropertyAmenity
    extra = 1

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('title', 'location', 'property_type', 'price', 'bedrooms', 'bathrooms', 'is_available', 'is_featured', 'rating', 'review_count')
    list_filter = ('property_type', 'is_available', 'is_featured', 'bedrooms', 'bathrooms', 'city', 'state', 'division', 'district')
    search_fields = ('title', 'location', 'address', 'description')
    list_editable = ('is_available', 'is_featured')
    inlines = [PropertyAmenityInline]
    readonly_fields = ('created_at', 'updated_at', 'rating', 'review_count')
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'property_type', 'status', 'featured_tag')
        }),
        ('Pricing & Location', {
            'fields': ('price', 'location', 'address', 'division', 'district', 'thana', 'postcode', 'city', 'state', 'country')
        }),
        ('Property Details', {
            'fields': ('bedrooms', 'bathrooms', 'square_feet', 'year_built', 'parking_spaces')
        }),
        ('Media', {
            'fields': ('main_image', 'virtual_tour_url', 'floor_plan_image')
        }),
        ('Relations', {
            'fields': ('agent', 'owner')
        }),
        ('Rules & Availability', {
            'fields': ('property_rules', 'availabilities', 'lease_term', 'security_deposit', 'application_fee')
        }),
        ('Policies', {
            'fields': ('pets_allowed', 'smoking_allowed', 'parties_allowed', 'quiet_hours')
        }),
        ('Status', {
            'fields': ('is_featured', 'is_available')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Make JSON fields use Textarea for easier editing in admin
        if 'property_rules' in form.base_fields:
            form.base_fields['property_rules'].widget = admin.widgets.AdminTextareaWidget(attrs={'rows': 3, 'cols': 40})
        if 'availabilities' in form.base_fields:
            form.base_fields['availabilities'].widget = admin.widgets.AdminTextareaWidget(attrs={'rows': 3, 'cols': 40})
        return form


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('property', 'user', 'rating', 'is_verified', 'created_at')
    list_filter = ('rating', 'is_verified', 'created_at', 'property')
    search_fields = ('property__title', 'user__username', 'comment')
    readonly_fields = ('created_at', 'updated_at')
    list_editable = ('is_verified',)  # Allow quick verification
    actions = ['mark_verified', 'mark_unverified']

    def mark_verified(self, request, queryset):
        queryset.update(is_verified=True)
    mark_verified.short_description = "Mark selected reviews as verified"

    def mark_unverified(self, request, queryset):
        queryset.update(is_verified=False)
    mark_unverified.short_description = "Mark selected reviews as unverified"
