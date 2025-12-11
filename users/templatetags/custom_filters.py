from django import template

register = template.Library()
@register.filter
def multiply(value, arg):
    """Multiply the value by the argument."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def get_rating_count(reviews, rating_value):
    """Count reviews with specific rating."""
    try:
        return sum(1 for r in reviews if r.rating == rating_value)
    except:
        return 0

@register.filter
def get_average_rating(reviews):
    """Calculate average rating from reviews."""
    try:
        if reviews:
            total = sum(r.rating for r in reviews)
            return round(total / len(reviews), 1)
        return 0
    except:
        return 0
    
@register.filter
def get_item(dictionary, key):
    """Get dictionary item by key in templates."""
    return dictionary.get(key, 0)