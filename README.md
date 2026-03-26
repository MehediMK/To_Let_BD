# Rent&Stay - Django Rental Property Platform

A modern, responsive rental property platform built with Django and Tailwind CSS.

## Features

- Browse featured rental properties
- Advanced search with filters (location, property type, price range)
- Property detail pages with agent information
- Responsive design (mobile, tablet, desktop)
- Admin interface to manage properties and agents
- Image upload support for properties and agents

## Tech Stack

- **Backend**: Django 5.0
- **Frontend**: Tailwind CSS (via CDN)
- **Database**: SQLite (development)
- **Media**: Pillow for image handling

## Project Structure

```
rentstay/
├── properties/          # Django app
│   ├── admin.py        # Admin configuration
│   ├── models.py       # Property and Agent models
│   ├── views.py        # View functions
│   ├── urls.py         # App URLs
│   ├── context_processors.py  # Global template context
│   └── migrations/     # Database migrations
├── rentstay/           # Django project
│   ├── settings.py     # Project settings
│   ├── urls.py         # Main URLs
│   └── wsgi.py         # WSGI config
├── templates/          # HTML templates
│   ├── base.html       # Base template
│   ├── index.html      # Homepage
│   ├── property_detail.html
│   └── search.html
├── static/             # Static files
│   ├── css/custom.css
│   └── js/main.js
├── media/              # Uploaded media (created automatically)
├── templates/          # Django templates
├── db.sqlite3          # SQLite database (created after migrations)
├── manage.py           # Django management script
├── requirements.txt    # Python dependencies
└── .gitignore          # Git ignore file
```

## Setup Instructions

### Prerequisites

- Python 3.8+
- pip (Python package manager)

### Installation

1. **Clone or download the project**

2. **Create virtual environment** (recommended):
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # Mac/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Apply migrations**:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Create superuser** (for admin access):
   ```bash
   python manage.py createsuperuser
   # Follow prompts to create admin account
   ```

6. **Run development server**:
   ```bash
   python manage.py runserver
   ```

7. **Open browser** and navigate to:
   - Homepage: http://127.0.0.1:8000/
   - Admin: http://127.0.0.1:8000/admin/

## Adding Properties via Admin

1. Go to http://127.0.0.1:8000/admin/
2. Login with your superuser credentials
3. Click "Agents" and add agent information (optional but recommended)
4. Click "Properties" and add:
   - Title
   - Description
   - Property type (Apartment, House, Villa, Studio, Penthouse)
   - Price (monthly rent)
   - Location
   - Bedrooms, Bathrooms, Square feet
   - Main image (upload)
   - Agent (assign if created)
   - Featured tag (optional: Featured, Premium, New, Popular, Beachfront)
   - Mark as "Featured" for homepage display

## Customization

### Tailwind CSS

The project uses Tailwind CSS via CDN. For production, consider:
1. Installing Tailwind via npm: `npm install tailwindcss`
2. Setting up a build process with PostCSS
3. Or using the Django Tailwind package

### Media Files

Uploaded images are stored in the `media/` directory. Make sure this directory is writable by Django.

### Adding New Property Types

Edit `properties/models.py`:
```python
PROPERTY_TYPES = (
    ('apartment', 'Apartment'),
    ('house', 'House'),
    ('villa', 'Villa'),
    ('studio', 'Studio'),
    ('penthouse', 'Penthouse'),
    # Add your new type here
)
```

Then run migrations:
```bash
python manage.py makemigrations properties
python manage.py migrate
```

## Deployment Checklist

- [ ] Set `DEBUG = False` in production
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Set up a production database (PostgreSQL recommended)
- [ ] Configure static and media file serving (WhiteNoise or S3)
- [ ] Use environment variables for secrets (SECRET_KEY, database credentials)
- [ ] Set up HTTPS
- [ ] Configure email backend
- [ ] Enable Django security middleware
- [ ] Run collectstatic if using WhiteNoise

## API Endpoints

- `GET /` - Homepage with featured properties
- `GET /search/` - Search properties with filters
- `GET /property/<id>/` - Property detail page
- `POST /search/` - Search form submission

## Future Enhancements

- User authentication (tenants and landlords)
- Property favorites/wishlist
- Advanced booking system
- Payment integration for rent payments
- Property reviews and ratings
- Map-based search
- Email notifications for new listings
- REST API for mobile app

## License

This project is open source and available for educational purposes.

## Support

For issues or questions, please open an issue in the repository.
