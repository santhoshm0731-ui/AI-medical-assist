from django import template

register = template.Library()

@register.filter
def underscore_to_space(value):
    """Convert underscores to spaces and capitalize."""
    if not isinstance(value, str):
        return value
    return value.replace("_", " ").capitalize()
