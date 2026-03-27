from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Count, Max
from django.core.paginator import Paginator
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.contrib.auth.models import User
from .models import Property, Amenity, PropertyImage, Inquiry, Favorite, PropertyAmenity, UserProfile, Review, Message, Notification, PushNotification
from .forms import SignUpForm, SignInForm, PropertyForm, PropertyImageForm, InquiryForm, UserProfileForm, ReviewForm, MessageForm
from .rate_limit import rate_limit
from .email_verification import send_verification_email, verify_email_token

def home(request):
    featured_properties = Property.objects.filter(
        is_available=True
    ).select_related('agent', 'owner').prefetch_related('property_amenities__amenity').order_by('-is_featured', '-rating', '-created_at')[:12]

    total_properties = Property.objects.filter(is_available=True).count()
    total_agents_count = Property.objects.filter(agent__isnull=False).values('agent').distinct().count()

    # Get popular locations
    popular_locations = Property.objects.filter(is_available=True)\
        .values('location').annotate(count=Count('id'))\
        .order_by('-count')[:5]

    # Get property types count
    property_types_count = Property.objects.filter(is_available=True)\
        .values('property_type').annotate(count=Count('id'))\
        .order_by('-count')

    context = {
        'featured_properties': featured_properties,
        'total_properties': total_properties,
        'total_agents': total_agents_count,
        'popular_locations': popular_locations,
        'property_types_count': property_types_count,
    }
    return render(request, 'index.html', context)

def property_detail(request, pk):
    # Get property without is_available filter initially
    property_obj = get_object_or_404(
        Property.objects.select_related('agent', 'owner'),
        pk=pk
    )

    # Check if user has permission to view this property
    can_view = property_obj.is_available
    if request.user.is_authenticated:
        # Owner can always view
        if request.user == property_obj.owner:
            can_view = True
        # User with inquiry can view
        elif Inquiry.objects.filter(property=property_obj, email=request.user.email).exists():
            can_view = True

    if not can_view:
        messages.error(request, 'This property is no longer available.')
        return redirect('home')

    # Increment view count
    property_obj.views = getattr(property_obj, 'views', 0) + 1
    property_obj.save(update_fields=['views'] if 'views' in [f.name for f in Property._meta.fields] else [])

    # Get related properties (same location, different type) with prefetch
    related_properties = Property.objects.filter(
        location=property_obj.location,
        is_available=True
    ).select_related('agent', 'owner').prefetch_related('property_amenities__amenity').exclude(pk=property_obj.pk)[:3]

    # Check if property is favorited
    is_favorited = False
    if request.user.is_authenticated:
        is_favorited = Favorite.objects.filter(
            user=request.user,
            property=property_obj
        ).exists()

    # Get all amenities for this property
    amenities = property_obj.property_amenities.select_related('amenity').all()

    # Get reviews with pagination (show all reviews)
    reviews_list = property_obj.reviews.select_related('user').order_by('-created_at')
    review_page = request.GET.get('review_page', 1)
    reviews_paginator = Paginator(reviews_list, 10)
    reviews = reviews_paginator.get_page(review_page)

    # Check if current user has already reviewed
    user_review = None
    if request.user.is_authenticated:
        user_review = Review.objects.filter(property=property_obj, user=request.user).first()

    context = {
        'property': property_obj,
        'related_properties': related_properties,
        'is_favorited': is_favorited,
        'amenities': amenities,
        'reviews': reviews,
        'user_review': user_review,
        'reviews_paginator': reviews_paginator if 'reviews_paginator' in locals() else None,
    }
    return render(request, 'property_detail.html', context)

def search(request):
    query = request.GET.get('q', '')
    property_type = request.GET.get('property_type', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    min_price_per_sqft = request.GET.get('min_price_per_sqft', '')
    max_price_per_sqft = request.GET.get('max_price_per_sqft', '')
    bedrooms = request.GET.get('bedrooms', '')
    bathrooms = request.GET.get('bathrooms', '')
    sort_by = request.GET.get('sort', 'newest')  # newest, price_low, price_high, price_per_sqft_low, price_per_sqft_high, rating
    page = request.GET.get('page', 1)

    properties = Property.objects.filter(is_available=True).select_related('agent', 'owner').prefetch_related('property_amenities__amenity')

    # Apply filters
    if query:
        properties = properties.filter(
            Q(title__icontains=query) |
            Q(location__icontains=query) |
            Q(description__icontains=query) |
            Q(address__icontains=query)
        )

    if property_type:
        properties = properties.filter(property_type=property_type)

    if min_price and min_price.isdigit():
        properties = properties.filter(price__gte=min_price)
    if max_price and max_price.isdigit():
        properties = properties.filter(price__lte=max_price)

    # Filter by price per square foot (annotate with calculated value)
    if min_price_per_sqft and min_price_per_sqft.replace('.', '').isdigit():
        properties = properties.filter(price__gt=0, square_feet__gt=0)
        properties = properties.extra(
            where=["price / square_feet >= %s"],
            params=[float(min_price_per_sqft)]
        )
    if max_price_per_sqft and max_price_per_sqft.replace('.', '').isdigit():
        properties = properties.filter(price__gt=0, square_feet__gt=0)
        properties = properties.extra(
            where=["price / square_feet <= %s"],
            params=[float(max_price_per_sqft)]
        )

    if bedrooms and bedrooms.isdigit():
        properties = properties.filter(bedrooms=bedrooms)
    if bathrooms and bathrooms.replace('.', '').isdigit():
        properties = properties.filter(bathrooms__gte=bathrooms)

    # Filter by amenities
    amenities_list = request.GET.getlist('amenities')
    if amenities_list:
        for amenity_id in amenities_list:
            if amenity_id.isdigit():
                properties = properties.filter(amenities=amenity_id)
        properties = properties.distinct()

    # Apply sorting
    if sort_by == 'price_low':
        properties = properties.order_by('price')
    elif sort_by == 'price_high':
        properties = properties.order_by('-price')
    elif sort_by == 'price_per_sqft_low':
        properties = properties.filter(price__gt=0, square_feet__gt=0).extra(
            select={'price_per_sqft': 'price / square_feet'}
        ).order_by('price_per_sqft')
    elif sort_by == 'price_per_sqft_high':
        properties = properties.filter(price__gt=0, square_feet__gt=0).extra(
            select={'price_per_sqft': 'price / square_feet'}
        ).order_by('-price_per_sqft')
    elif sort_by == 'rating':
        properties = properties.order_by('-rating', '-review_count')
    else:  # newest
        properties = properties.order_by('-created_at')

    # Pagination
    paginator = Paginator(properties, 12)  # 12 per page
    properties_page = paginator.get_page(page)

    # Get all amenities for filtering
    all_amenities = Amenity.objects.all().order_by('name')

    context = {
        'properties': properties_page,
        'query': query,
        'property_type': property_type,
        'min_price': min_price,
        'max_price': max_price,
        'min_price_per_sqft': min_price_per_sqft,
        'max_price_per_sqft': max_price_per_sqft,
        'bedrooms': bedrooms,
        'bathrooms': bathrooms,
        'sort_by': sort_by,
        'total_count': paginator.count,
        'all_amenities': all_amenities,
        'selected_amenities': [int(a) for a in amenities_list if a.isdigit()],
    }
    return render(request, 'search.html', context)

@rate_limit('signup', limit=5, period=300)  # 5 attempts per 5 minutes
def signup_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = SignUpForm(request.POST, request=request)
        if form.is_valid():
            user = form.save()
            # Create user profile
            profile = UserProfile.objects.create(user=user)

            # Send verification email (non-blocking)
            try:
                send_verification_email(request, profile)
            except Exception as e:
                # Log error but don't prevent signup
                print(f"Failed to send verification email: {e}")

            login(request, user)
            messages.success(request, 'Account created successfully! Please verify your email.')
            return redirect('home')
    else:
        form = SignUpForm(request=request)

    context = {'form': form}
    return render(request, 'signup.html', context)

def signin_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = SignInForm(request, data=request.POST)
        if form.is_valid():
            phone = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=phone, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, 'Logged in successfully!')
                next_url = request.GET.get('next', 'home')
                return redirect(next_url)
            else:
                messages.error(request, 'Invalid phone number or password.')
        else:
            messages.error(request, 'Invalid credentials.')
    else:
        form = SignInForm()

    context = {'form': form}
    return render(request, 'signin.html', context)

def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('home')

@login_required
def list_property_view(request):
    if request.method == 'POST':
        form = PropertyForm(request.POST, request.FILES)
        if form.is_valid():
            property_obj = form.save(commit=False)
            property_obj.owner = request.user
            property_obj.save()
            form.save_m2m()  # Save amenities
            messages.success(request, 'Property listed successfully!')
            return redirect('property_detail', pk=property_obj.pk)
    else:
        form = PropertyForm()

    context = {'form': form}
    return render(request, 'list_property.html', context)

@login_required
def my_properties_view(request):
    properties = Property.objects.filter(owner=request.user).order_by('-created_at')
    context = {'properties': properties}
    return render(request, 'my_properties.html', context)


@login_required
def duplicate_property_view(request, pk):
    """Duplicate an existing property (copy all data except unique fields)"""
    original = get_object_or_404(Property, pk=pk, owner=request.user)

    # Create a copy of the property
    # Get all field values except for auto fields (id, created_at, updated_at, views, rating, review_count)
    field_values = {}
    for field in original._meta.fields:
        if field.auto_created or field.name in ['id', 'created_at', 'updated_at', 'views', 'rating', 'review_count']:
            continue
        field_values[field.name] = getattr(original, field.name)

    # Create new property with a modified title
    field_values['title'] = f"Copy of {original.title}"
    new_property = Property(**field_values)
    new_property.save()

    # Copy many-to-many relationships through the through model

    # Copy amenities (through PropertyAmenity model)
    old_amenities = PropertyAmenity.objects.filter(property=original)
    for old_pa in old_amenities:
        PropertyAmenity.objects.create(
            property=new_property,
            amenity=old_pa.amenity,
            notes=old_pa.notes,
            order=old_pa.order
        )

    # Copy gallery images (PropertyImage model)
    old_images = PropertyImage.objects.filter(property=original)
    for old_img in old_images:
        # Duplicate the image file by creating a new instance
        PropertyImage.objects.create(
            property=new_property,
            image=old_img.image,
            caption=old_img.caption,
            order=old_img.order
        )

    messages.success(request, f'Property "{original.title}" duplicated successfully! You can now edit the copy.')
    return redirect('edit_property', pk=new_property.pk)


@login_required
def bulk_property_actions(request):
    """Handle bulk actions on multiple properties"""
    if request.method != 'POST':
        return redirect('my_properties')

    action = request.POST.get('action')
    selected_ids = request.POST.getlist('selected_properties')

    if not selected_ids:
        messages.error(request, 'No properties selected.')
        return redirect('my_properties')

    # Get properties owned by current user
    properties = Property.objects.filter(pk__in=selected_ids, owner=request.user)
    count = properties.count()

    if count == 0:
        messages.error(request, 'No valid properties found.')
        return redirect('my_properties')

    if action == 'publish':
        updated = properties.update(is_available=True)
        messages.success(request, f'{updated} property{"es" if updated > 1 else ""} published successfully.')
    elif action == 'unpublish':
        updated = properties.update(is_available=False)
        messages.success(request, f'{updated} property{"es" if updated > 1 else ""} unpublished successfully.')
    elif action == 'delete':
        properties.delete()
        messages.success(request, f'{count} property{"ies" if count > 1 else "y"} deleted successfully.')
    else:
        messages.error(request, 'Invalid action.')

    return redirect('my_properties')


@login_required
def dashboard_home(request):
    """Owner dashboard with statistics and recent activity"""
    from django.db.models import Sum, Count, Avg, Q
    from django.utils import timezone
    from datetime import timedelta

    # Get user's properties with prefetched related data for performance
    my_properties = Property.objects.filter(owner=request.user).prefetch_related('inquiries', 'favorited_by', 'reviews')

    # Total statistics
    total_properties = my_properties.count()
    active_properties = my_properties.filter(is_available=True).count()
    total_views = my_properties.aggregate(Sum('views'))['views__sum'] or 0
    total_inquiries = Inquiry.objects.filter(property__owner=request.user).count()
    total_reviews = Review.objects.filter(property__owner=request.user).count()
    total_favorites = Favorite.objects.filter(property__owner=request.user).count()

    # Recent activity (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_inquiries = Inquiry.objects.filter(
        property__owner=request.user,
        created_at__gte=thirty_days_ago
    ).count()
    recent_views = Property.objects.filter(
        owner=request.user,
        updated_at__gte=thirty_days_ago
    ).count()

    # Calculate average ratings
    avg_rating = my_properties.aggregate(Avg('rating'))['rating__avg'] or 0

    # Top performing properties by views
    top_by_views = my_properties.order_by('-views')[:5]

    # Top performing properties by inquiries
    top_by_inquiries = my_properties.annotate(
        inquiry_count=Count('inquiries')
    ).order_by('-inquiry_count')[:5]

    # Recent inquiries
    recent_inquiries_list = Inquiry.objects.filter(
        property__owner=request.user
    ).select_related('property').order_by('-created_at')[:10]

    # Property status breakdown
    status_breakdown = my_properties.values('status').annotate(count=Count('status'))

    # Monthly views trend (last 6 months) - approximate using created_at of PropertyVisit if we had that model
    # For now, we'll show property listing dates as a placeholder

    context = {
        'total_properties': total_properties,
        'active_properties': active_properties,
        'total_views': total_views,
        'total_inquiries': total_inquiries,
        'total_reviews': total_reviews,
        'total_favorites': total_favorites,
        'recent_inquiries': recent_inquiries,
        'recent_views': recent_views,
        'avg_rating': round(avg_rating, 1),
        'top_by_views': top_by_views,
        'top_by_inquiries': top_by_inquiries,
        'recent_inquiries_list': recent_inquiries_list,
        'status_breakdown': status_breakdown,
        'my_properties': my_properties,  # Add missing context variable
    }
    return render(request, 'dashboard.html', context)

@login_required
def edit_property_view(request, pk):
    property_obj = get_object_or_404(Property, pk=pk, owner=request.user)

    if request.method == 'POST':
        form = PropertyForm(request.POST, request.FILES, instance=property_obj)
        if form.is_valid():
            property_obj = form.save()
            messages.success(request, 'Property updated successfully!')
            return redirect('my_properties')
    else:
        form = PropertyForm(instance=property_obj)

    context = {'form': form, 'property': property_obj}
    return render(request, 'edit_property.html', context)


@login_required
def delete_property_view(request, pk):
    property_obj = get_object_or_404(Property, pk=pk, owner=request.user)

    if request.method == 'POST':
        property_obj.delete()
        messages.success(request, 'Property deleted successfully!')
        return redirect('my_properties')

    context = {'property': property_obj}
    return render(request, 'delete_property.html', context)

@login_required
def profile_view(request):
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            # Update user info
            request.user.first_name = request.POST.get('first_name', '')
            request.user.last_name = request.POST.get('last_name', '')
            request.user.email = request.POST.get('email', '')
            request.user.save()
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=profile)

    context = {
        'profile': profile,
        'form': form,
    }
    return render(request, 'profile.html', context)

@login_required
def add_property_image(request, pk):
    property_obj = get_object_or_404(Property, pk=pk, owner=request.user)

    if request.method == 'POST':
        form = PropertyImageForm(request.POST, request.FILES)
        if form.is_valid():
            image = form.save(commit=False)
            image.property = property_obj

            # Auto-assign order if not provided or if it conflicts
            submitted_order = form.cleaned_data.get('order')
            if submitted_order is not None:
                # Check if this order already exists for this property
                existing = PropertyImage.objects.filter(property=property_obj, order=submitted_order).exists()
                if existing:
                    # Assign next available order
                    max_order = PropertyImage.objects.filter(property=property_obj).aggregate(
                        max_order=Max('order')
                    )['max_order'] or 0
                    image.order = max_order + 1
                else:
                    image.order = submitted_order
            else:
                # No order provided, assign next available
                max_order = PropertyImage.objects.filter(property=property_obj).aggregate(
                    max_order=Max('order')
                )['max_order'] or 0
                image.order = max_order + 1

            image.save()
            messages.success(request, 'Image added successfully!')
            return redirect('edit_property', pk=pk)
    else:
        # Pre-populate with next order number
        max_order = PropertyImage.objects.filter(property=property_obj).aggregate(
            max_order=Max('order')
        )['max_order'] or 0
        form = PropertyImageForm(initial={'order': max_order + 1})

    context = {'form': form, 'property': property_obj}
    return render(request, 'add_image.html', context)

@login_required
def delete_property_image(request, pk):
    image = get_object_or_404(PropertyImage, pk=pk, property__owner=request.user)
    property_pk = image.property.pk
    image.delete()
    messages.success(request, 'Image deleted successfully!')
    return redirect('edit_property', pk=property_pk)

@login_required
def toggle_favorite(request, pk):
    property_obj = get_object_or_404(Property, pk=pk)
    favorite, created = Favorite.objects.get_or_create(
        user=request.user,
        property=property_obj
    )
    if not created:
        favorite.delete()
        messages.info(request, 'Removed from favorites')
        is_favorited = False
    else:
        messages.success(request, 'Added to favorites')
        is_favorited = True

    # Redirect back or return JSON for AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'is_favorited': is_favorited, 'count': property_obj.favorited_by.count()})
    return redirect('property_detail', pk=pk)

@login_required
def favorites_view(request):
    favorites = Favorite.objects.filter(user=request.user).select_related('property').order_by('-created_at')
    context = {'favorites': favorites}
    return render(request, 'favorites.html', context)

@login_required
@rate_limit('inquiry', limit=10, period=300)  # 10 inquiries per 5 minutes
def submit_inquiry(request, pk):
    property_obj = get_object_or_404(Property, pk=pk)

    if request.method == 'POST':
        form = InquiryForm(request.POST)
        if form.is_valid():
            inquiry = form.save(commit=False)
            inquiry.property = property_obj
            inquiry.save()
            messages.success(request, 'Your inquiry has been submitted successfully! The property owner will contact you soon.')
            return redirect('property_detail', pk=pk)
    else:
        # Pre-fill with user info if logged in
        initial_data = {
            'name': f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
            'email': request.user.email or '',
        }
        if hasattr(request.user, 'profile') and request.user.profile.phone:
            initial_data['phone'] = request.user.profile.phone
        form = InquiryForm(initial=initial_data)

    context = {
        'form': form,
        'property': property_obj
    }
    return render(request, 'submit_inquiry.html', context)

@login_required
def my_inquiries_view(request):
    """View inquiries where current user is the tenant (email matches)"""
    inquiries = Inquiry.objects.filter(email=request.user.email).order_by('-created_at')
    context = {'inquiries': inquiries}
    return render(request, 'my_inquiries.html', context)

@login_required
def owner_inquiries_view(request):
    """View inquiries for properties owned by current user"""
    # Get all inquiries for properties owned by this user
    inquiries_list = Inquiry.objects.filter(property__owner=request.user).select_related('property').order_by('-created_at')

    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(inquiries_list, 15)  # 15 per page
    inquiries = paginator.get_page(page)

    # Handle status update via POST
    if request.method == 'POST':
        inquiry_id = request.POST.get('inquiry_id')
        new_status = request.POST.get('status')
        if inquiry_id and new_status:
            inquiry = get_object_or_404(Inquiry, pk=inquiry_id, property__owner=request.user)
            old_status = inquiry.status
            inquiry.status = new_status
            inquiry.save()
            messages.success(request, f'Inquiry status updated from "{inquiry.get_status_display()}" to "{new_status.title()}".')
            # Redirect to avoid resubmission
            return redirect('owner_inquiries')

    context = {
        'inquiries': inquiries,
        'status_choices': Inquiry.STATUS_CHOICES,
    }
    return render(request, 'owner_inquiries.html', context)


@login_required
def add_review_view(request, pk):
    property_obj = get_object_or_404(Property, pk=pk, is_available=True)

    # Check if user already has a review for this property
    existing_review = Review.objects.filter(property=property_obj, user=request.user).first()
    if existing_review:
        messages.warning(request, 'You have already reviewed this property.')
        return redirect('property_detail', pk=pk)

    if request.method == 'POST':
        form = ReviewForm(request.POST, property=property_obj, user=request.user)
        if form.is_valid():
            review = form.save(commit=False)
            review.property = property_obj
            review.user = request.user
            # Mark as verified if user has an inquiry that was approved/rented
            has_inquiry = property_obj.inquiries.filter(
                email=request.user.email,
                status__in=['approved', 'rented']
            ).exists()
            review.is_verified = has_inquiry
            review.save()
            messages.success(request, 'Thank you for your review!')
            return redirect('property_detail', pk=pk)
    else:
        form = ReviewForm()

    context = {
        'form': form,
        'property': property_obj
    }
    return render(request, 'add_review.html', context)

@login_required
def delete_review_view(request, pk):
    review = get_object_or_404(Review, pk=pk, user=request.user)
    property_pk = review.property.pk
    review.delete()
    messages.success(request, 'Review deleted successfully.')
    return redirect('property_detail', pk=property_pk)

@login_required
def respond_review_view(request, pk):
    """Property owner responds to a review"""
    review = get_object_or_404(Review, pk=pk)

    # Check if current user is the property owner
    if request.user != review.property.owner:
        messages.error(request, 'You do not have permission to respond to this review.')
        return redirect('property_detail', pk=review.property.pk)

    if request.method == 'POST':
        response_text = request.POST.get('owner_response', '').strip()
        if response_text:
            review.owner_response = response_text
            review.owner_response_date = timezone.now()
            review.save()
            messages.success(request, 'Response added successfully.')
        else:
            messages.error(request, 'Response cannot be empty.')

    return redirect('property_detail', pk=review.property.pk)


@login_required
def send_verification_view(request):
    """Send email verification link to current user"""
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)

    if profile.email_verified:
        messages.info(request, 'Your email is already verified.')
    else:
        try:
            send_verification_email(request, profile)
            messages.success(request, 'Verification email sent! Please check your inbox.')
        except Exception as e:
            messages.error(request, f'Failed to send verification email: {str(e)}')

    # Redirect back to profile or next URL
    next_url = request.GET.get('next', 'profile')
    return redirect(next_url)

def verify_email_view(request, token):
    """Verify email token"""
    user = verify_email_token(token)
    if user:
        messages.success(request, 'Email verified successfully! Your account is now active.')
        # Auto login if not already logged in
        if not request.user.is_authenticated:
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)
    else:
        messages.error(request, 'Invalid or expired verification link. Please request a new verification email.')

    return redirect('profile')


@login_required
def notifications_view(request):
    """View all notifications for the current user"""
    notifications = request.user.notifications.all()
    unread_count = notifications.filter(is_read=False).count()

    # Handle mark as read/unread actions
    if request.method == 'POST':
        action = request.POST.get('action')
        notification_id = request.POST.get('notification_id')
        if notification_id and action:
            try:
                notification = Notification.objects.get(pk=notification_id, user=request.user)
                if action == 'mark_read':
                    notification.mark_as_read()
                    messages.success(request, 'Notification marked as read.')
                elif action == 'mark_unread':
                    notification.mark_as_unread()
                    messages.success(request, 'Notification marked as unread.')
                elif action == 'delete':
                    notification.delete()
                    messages.success(request, 'Notification deleted.')
            except Notification.DoesNotExist:
                messages.error(request, 'Notification not found.')
        return redirect('notifications')

    context = {
        'notifications': notifications,
        'unread_count': unread_count,
    }
    return render(request, 'notifications.html', context)


@login_required
def mark_notification_read(request, pk):
    """Mark a single notification as read (AJAX)"""
    if request.method == 'POST':
        try:
            notification = Notification.objects.get(pk=pk, user=request.user)
            notification.mark_as_read()
            return JsonResponse({'success': True, 'unread_count': request.user.notifications.filter(is_read=False).count()})
        except Notification.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Notification not found'})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
def inbox_view(request):
    """View received messages"""
    messages = Message.objects.filter(receiver=request.user).select_related('sender', 'related_property', 'parent_message').order_by('-sent_at')
    context = {'messages': messages}
    return render(request, 'inbox.html', context)


@login_required
def outbox_view(request):
    """View sent messages"""
    messages = Message.objects.filter(sender=request.user).select_related('receiver', 'related_property', 'parent_message').order_by('-sent_at')
    context = {'messages': messages}
    return render(request, 'outbox.html', context)


@login_required
def send_message_view(request, receiver_id=None, property_id=None):
    """Send a new message"""
    initial = {}
    property_obj = None

    # Handle property context from URL
    if property_id:
        try:
            property_obj = Property.objects.select_related('agent', 'owner').get(pk=property_id)
            # Ensure property has an owner (required for messaging)
            if not property_obj.owner:
                messages.error(request, 'Cannot send message: This property does not have an owner assigned.')
                return redirect('property_detail', pk=property_id)
            initial['property'] = property_obj
        except Property.DoesNotExist:
            messages.error(request, 'Property not found.')
            return redirect('home')

    # Handle explicit receiver_id (takes precedence if both provided)
    if receiver_id:
        try:
            receiver = User.objects.get(pk=receiver_id)
            initial['receiver'] = receiver
        except User.DoesNotExist:
            pass

    if request.method == 'POST':
        form = MessageForm(request.POST, sender=request.user, property=property_obj)
        if form.is_valid():
            message = form.save(commit=True)
            messages.success(request, 'Message sent successfully!')
            # If property context, redirect to property detail; else to outbox
            if message.related_property:
                return redirect('property_detail', pk=message.related_property.pk)
            return redirect('outbox')
    else:
        form = MessageForm(initial=initial, sender=request.user, property=property_obj)

    context = {
        'form': form,
        'property': property_obj
    }
    return render(request, 'send_message.html', context)


@login_required
def reply_message_view(request, pk):
    """Reply to an existing message"""
    parent_message = get_object_or_404(Message, pk=pk, receiver=request.user)
    if request.method == 'POST':
        form = MessageForm(request.POST, sender=request.user)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.receiver = parent_message.sender
            reply.related_property = parent_message.related_property
            reply.parent_message = parent_message
            reply.save()
            messages.success(request, 'Reply sent successfully!')
            return redirect('inbox')
    else:
        initial = {
            'subject': f'Re: {parent_message.subject}' if not parent_message.subject.startswith('Re:') else parent_message.subject,
            'receiver': parent_message.sender,
            'property': parent_message.related_property,
        }
        form = MessageForm(initial=initial, sender=request.user)

    context = {'form': form, 'parent_message': parent_message}
    return render(request, 'reply_message.html', context)


@login_required
def delete_message_view(request, pk):
    """Delete a message (sender or receiver can delete)"""
    message = get_object_or_404(Message, pk=pk)
    # Check if user is sender or receiver
    if request.user != message.sender and request.user != message.receiver:
        messages.error(request, 'You do not have permission to delete this message.')
        return redirect('inbox')

    if request.method == 'POST':
        message.delete()
        messages.success(request, 'Message deleted successfully.')
        # Redirect based on where user came from
        if request.user == message.sender:
            return redirect('outbox')
        else:
            return redirect('inbox')

    context = {'message': message}
    return render(request, 'delete_message.html', context)

