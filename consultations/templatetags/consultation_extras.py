from django import template

register = template.Library()

@register.filter
def dict_key(d, key):
    """
    Template filter to look up a key in a dictionary.
    Usage: {{ pending_follow_ups|dict_key:c.pk }}
    Returns the value for the given key, or None if not found.
    """
    try:
        return d.get(key)
    except (AttributeError, TypeError):
        return None
