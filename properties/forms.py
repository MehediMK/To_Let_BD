import random
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Property, Amenity, PropertyAmenity, Inquiry, UserProfile, PropertyImage, Favorite, Review, Message
from .validators import compress_image
import json

class SignUpForm(UserCreationForm):
    error_css_class = 'border-red-500'

    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none',
            'placeholder': 'your.email@example.com'
        })
    )
    first_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none',
            'placeholder': 'First Name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none',
            'placeholder': 'Last Name'
        })
    )
    captcha = forms.IntegerField(
        label="Human Verification",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none',
            'placeholder': 'Enter the sum'
        })
    )

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "password1", "password2")

    def __init__(self, *args, **kwargs):
        # Pop request from kwargs if present
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Phone Number'
        self.fields['username'].widget.attrs.update({
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none',
            'placeholder': 'Enter your phone number (e.g., +1234567890)'
        })
        self.fields['username'].help_text = None

        # Generate CAPTCHA question and store answer
        self.captcha_num1 = random.randint(1, 20)
        self.captcha_num2 = random.randint(1, 20)
        self.captcha_answer = self.captcha_num1 + self.captcha_num2

        # Store answer in session if request available
        if self.request:
            self.request.session['captcha_answer'] = self.captcha_answer

        # Update captcha label with question
        self.fields['captcha'].label = f"What is {self.captcha_num1} + {self.captcha_num2}?"

    def clean_username(self):
        username = self.cleaned_data.get('username')
        # Validate phone format: allow +, digits, length 9-15
        clean_phone = ''.join(filter(str.isdigit, username))
        if username.startswith('+'):
            clean_phone = '+' + clean_phone
        if not clean_phone or len(clean_phone.replace('+', '')) < 9 or len(clean_phone.replace('+', '')) > 15:
            raise forms.ValidationError("Enter a valid phone number (9-15 digits, optionally starting with +)")
        return username

    def clean_captcha(self):
        captcha = self.cleaned_data.get('captcha')
        # Get the correct answer from session
        correct_answer = None
        if self.request:
            correct_answer = self.request.session.get('captcha_answer')

        if correct_answer is None:
            raise forms.ValidationError("CAPTCHA expired. Please try again.")

        if captcha != correct_answer:
            # Clear the answer so they must try again
            if self.request:
                self.request.session.pop('captcha_answer', None)
            raise forms.ValidationError("Incorrect answer. Please try again.")

        # Clear used answer
        if self.request:
            self.request.session.pop('captcha_answer', None)

        return captcha

class SignInForm(AuthenticationForm):
    error_css_class = 'border-red-500'

    username = forms.CharField(
        label='Phone Number',
        max_length=254,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none',
            'placeholder': 'Enter your phone number'
        })
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none',
            'placeholder': 'Enter your password'
        })
    )

class InquiryForm(forms.ModelForm):
    error_css_class = 'border-red-500'

    class Meta:
        model = Inquiry
        fields = ['name', 'email', 'phone', 'message', 'move_in_date']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none',
                'placeholder': 'Your full name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none',
                'placeholder': 'your.email@example.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none',
                'placeholder': '+1234567890'
            }),
            'message': forms.Textarea(attrs={
                'rows': 4,
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none',
                'placeholder': 'Tell us about your interest in this property...'
            }),
            'move_in_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none'
            }),
        }

class UserProfileForm(forms.ModelForm):
    error_css_class = 'border-red-500'

    class Meta:
        model = UserProfile
        fields = ['phone', 'bio', 'avatar', 'date_of_birth', 'address', 'city', 'state', 'country', 'is_landlord']
        widgets = {
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none',
                'placeholder': '+1234567890'
            }),
            'bio': forms.Textarea(attrs={
                'rows': 4,
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none',
                'placeholder': 'Tell us about yourself...'
            }),
            'date_of_birth': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none'
            }),
            'address': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none',
                'placeholder': '123 Main St'
            }),
            'city': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none'
            }),
            'state': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none'
            }),
            'country': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none'
            }),
            'avatar': forms.ClearableFileInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none file:mr-4 file:py-2 file:px-4 file:border-0 file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100'
            }),
            'is_landlord': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500'
            }),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Compress avatar if provided
        avatar = self.cleaned_data.get('avatar')
        if avatar:
            compressed = compress_image(avatar)
            instance.avatar.save(
                avatar.name,
                compressed,
                save=False
            )

        if commit:
            instance.save()
        return instance

class PropertyForm(forms.ModelForm):
    error_css_class = 'border-red-500'

    amenities = forms.ModelMultipleChoiceField(
        queryset=Amenity.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'grid grid-cols-2 md:grid-cols-3 gap-3'
        }),
        required=False
    )

    class Meta:
        model = Property
        fields = [
            'title',
            'description',
            'property_type',
            'price',
            'location',
            'address',
            'division',
            'district',
            'thana',
            'postcode',
            'city',
            'state',
            'country',
            'bedrooms',
            'bathrooms',
            'square_feet',
            'year_built',
            'parking_spaces',
            'main_image',
            'virtual_tour_url',
            'virtual_tour_360',
            'floor_plan_image',
            'agent',
            'is_featured',
            'is_available',
            'lease_term',
            'security_deposit',
            'application_fee',
            'pets_allowed',
            'smoking_allowed',
            'parties_allowed',
            'quiet_hours',
            'amenities',
        ]
        widgets = {
            'description': forms.Textarea(attrs={
                'rows': 6,
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none',
                'placeholder': 'Detailed description of the property...'
            }),
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none',
                'placeholder': 'e.g., Modern Downtown Loft'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none',
                'placeholder': '25000',
                'step': '0.01',
                'min': 0
            }),
            'location': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none',
                'placeholder': 'e.g., Banani, Gulshan, Dhanmondi, Jessore'
            }),
            'address': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none',
                'placeholder': 'House number, road name'
            }),
            'division': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none bg-white'
            }),
            'district': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none',
                'placeholder': 'e.g., Dhaka, Chittagong'
            }),
            'thana': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none',
                'placeholder': 'e.g., Banani, Dhanmondi, Motijheel'
            }),
            'postcode': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none',
                'placeholder': 'e.g., 1212, 1000'
            }),
            'city': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none',
                'placeholder': 'e.g., Dhaka, Chittagong'
            }),
            'state': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none',
                'placeholder': 'NY'
            }),
            'country': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none',
                'placeholder': 'USA'
            }),
            'bedrooms': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none',
                'min': 0
            }),
            'bathrooms': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none',
                'step': '0.5',
                'min': 0
            }),
            'square_feet': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none',
                'min': 0
            }),
            'year_built': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none',
                'min': 1800,
                'max': 2025,
                'placeholder': 'e.g., 2010'
            }),
            'parking_spaces': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none',
                'min': 0
            }),
            'security_deposit': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none',
                'step': '0.01',
                'placeholder': '1000'
            }),
            'application_fee': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none',
                'step': '0.01',
                'placeholder': '50'
            }),
            'quiet_hours': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none',
                'placeholder': 'e.g., 10 PM - 7 AM'
            }),
            'lease_term': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none',
                'placeholder': 'e.g., 12 months'
            }),
            'virtual_tour_url': forms.URLInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none',
                'placeholder': 'https://youtube.com/watch?v=...'
            }),
            'property_type': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none bg-white'
            }),
            'featured_tag': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none bg-white'
            }),
            'pets_allowed': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none bg-white'
            }),
            'smoking_allowed': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none bg-white'
            }),
            'parties_allowed': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none bg-white'
            }),
            'main_image': forms.ClearableFileInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none file:mr-4 file:py-2 file:px-4 file:border-0 file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100'
            }),
            'floor_plan_image': forms.ClearableFileInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none file:mr-4 file:py-2 file:px-4 file:border-0 file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100'
            }),
            'agent': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none bg-white'
            }),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Initialize property_rules if not set
        if not instance.property_rules:
            instance.property_rules = {
                'pets_allowed': self.cleaned_data.get('pets_allowed', 'no'),
                'smoking_allowed': self.cleaned_data.get('smoking_allowed', 'no'),
                'parties_allowed': self.cleaned_data.get('parties_allowed', 'no'),
                'quiet_hours': self.cleaned_data.get('quiet_hours', ''),
            }

        # Compress main image if provided
        main_image = self.cleaned_data.get('main_image')
        if main_image:
            compressed = compress_image(main_image)
            instance.main_image.save(
                main_image.name,
                compressed,
                save=False
            )

        # Compress floor plan image if provided
        floor_plan = self.cleaned_data.get('floor_plan_image')
        if floor_plan:
            compressed = compress_image(floor_plan)
            instance.floor_plan_image.save(
                floor_plan.name,
                compressed,
                save=False
            )

        if commit:
            instance.save()
            self.save_m2m()
        return instance

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(
                choices=[(i, i) for i in range(1, 6)],
                attrs={
                    'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none bg-white'
                }
            ),
            'comment': forms.Textarea(attrs={
                'rows': 4,
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none',
                'placeholder': 'Share your experience with this property...'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.property = kwargs.pop('property', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

class PropertyImageForm(forms.ModelForm):
    error_css_class = 'border-red-500'

    class Meta:
        model = PropertyImage
        fields = ['image', 'caption', 'order']
        widgets = {
            'caption': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none',
                'placeholder': 'Image caption (optional)'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none',
                'min': 0
            }),
            'image': forms.ClearableFileInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none file:mr-4 file:py-2 file:px-4 file:border-0 file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100'
            }),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Compress image if provided
        image = self.cleaned_data.get('image')
        if image:
            compressed = compress_image(image)
            instance.image.save(
                image.name,
                compressed,
                save=False
            )

        if commit:
            instance.save()
        return instance


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['receiver', 'related_property', 'subject', 'body']
        widgets = {
            'receiver': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none bg-white'
            }),
            'related_property': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none bg-white'
            }),
            'subject': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none',
                'placeholder': 'Message subject'
            }),
            'body': forms.Textarea(attrs={
                'rows': 6,
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none',
                'placeholder': 'Write your message here...'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.sender = kwargs.pop('sender', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.sender:
            instance.sender = self.sender
        if commit:
            instance.save()
        return instance
