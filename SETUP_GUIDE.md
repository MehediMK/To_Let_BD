# Quick Setup Guide

Follow these steps to get your Rent&Stay Django application running:

## Step 1: Install Django & Dependencies

```bash
pip install django pillow
```

Or if using the requirements.txt:
```bash
pip install -r requirements.txt
```

## Step 2: Initialize Database

```bash
python manage.py makemigrations properties
python manage.py migrate
```

## Step 3: Create Admin User

```bash
python manage.py createsuperuser
```

Enter username, email, and password when prompted.

## Step 4: Run the Development Server

```bash
python manage.py runserver
```

Open your browser and go to:
- **Homepage**: http://127.0.0.1:8000/
- **Admin Panel**: http://127.0.0.1:8000/admin/

## Step 5: Add Sample Data (Optional)

1. Go to the admin panel
2. Create an Agent first (optional but recommended)
3. Add Properties:
   - Upload a main image (any JPG/PNG)
   - Fill in title, description, price, location
   - Set bedrooms, bathrooms, square feet
   - Assign an agent if created
   - Check "Featured" to show on homepage

## Troubleshooting

**Error: "No module named 'django'"**
Make sure Django is installed: `pip install django`

**Static files not loading**
- Tailwind CSS is loaded via CDN, so it should work immediately
- For uploaded images, make sure the `media/` directory exists

**Images not displaying**
- Check that `MEDIA_URL` and `MEDIA_ROOT` are set correctly in settings.py
- Ensure the `media/` directory exists and is writable

**Template errors**
- Make sure all templates are in the `templates/` directory (not inside app folders)
- Verify template inheritance is correct

## Project Directory Layout

Ensure your project structure looks like this:

```
D:\Mehedi\claude\
├── manage.py
├── rentstay\
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── properties\
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── context_processors.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── templates\
│   ├── base.html
│   ├── index.html
│   ├── property_detail.html
│   └── search.html
├── static\
│   ├── css\
│   │   └── custom.css
│   └── js\
│       └── main.js
└── media\  (will be created automatically)
```

## Need Help?

Check the full README.md for more detailed documentation.
