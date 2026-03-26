from .models import Property, Amenity

def property_types(request):
    return {
        'property_types': Property.PROPERTY_TYPES,
        'bd_divisions': Property._meta.get_field('division').choices,
    }

def all_amenities(request):
    return {
        'all_amenities': Amenity.objects.all().order_by('name')
    }
