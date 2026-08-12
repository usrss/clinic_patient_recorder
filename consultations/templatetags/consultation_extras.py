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


@register.filter
def option_selected(value, option):
    """
    Return the string 'selected' when *value* matches *option* (string
    comparison), otherwise an empty string. Used to pre-fill <option> tags
    in the prescription edit form.
    Usage: <option {{ form.field.value|option_selected:'500mg' }}>500mg</option>
    """
    return 'selected' if str(value or '') == str(option) else ''
