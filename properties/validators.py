from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from PIL import Image
import os

@deconstructible
class ImageValidator:
    """Validator for image files"""
    def __init__(self, max_size_mb=5, allowed_extensions=None):
        self.max_size_mb = max_size_mb
        self.allowed_extensions = allowed_extensions or ['jpg', 'jpeg', 'png', 'webp']

    def __call__(self, value):
        # Check file size
        if value.size > self.max_size_mb * 1024 * 1024:
            raise ValidationError(f'Image file too large (max {self.max_size_mb}MB)')

        # Check file extension
        ext = os.path.splitext(value.name)[1].lower().replace('.', '')
        if ext not in self.allowed_extensions:
            raise ValidationError(f'Unsupported file type. Allowed: {", ".join(self.allowed_extensions)}')

        # Verify it's actually an image
        try:
            img = Image.open(value)
            img.verify()
        except (IOError, SyntaxError) as e:
            raise ValidationError('Invalid image file') from e

        # Reset file pointer for later use
        value.seek(0)

def validate_image_size(value):
    """Simple validator for image size (5MB max)"""
    validator = ImageValidator(max_size_mb=5)
    validator(value)

def compress_image(image, quality=85, max_width=1920, max_height=1080):
    """
    Compress image and resize if too large
    Returns: BytesIO object with compressed image
    """
    from io import BytesIO
    from PIL import Image

    img = Image.open(image)

    # Convert to RGB if necessary (for PNG with transparency)
    if img.mode in ('RGBA', 'LA'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'RGBA':
            background.paste(img, mask=img.split()[-1])
        else:
            background.paste(img, mask=img)
        img = background
    elif img.mode != 'RGB':
        img = img.convert('RGB')

    # Resize if too large
    if img.width > max_width or img.height > max_height:
        img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

    # Save compressed image to BytesIO
    output = BytesIO()
    img.save(output, format='JPEG', quality=quality, optimize=True)
    output.seek(0)
    return output
