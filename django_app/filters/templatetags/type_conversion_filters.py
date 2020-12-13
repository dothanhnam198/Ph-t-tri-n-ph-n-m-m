from django import template

register = template.Library()


@register.filter(name='to_int')
def to_int(value):
    try:
        return int(value)
    except:
        return 0


@register.filter(name='to_string')
def to_string(value):
    try:
        return str(value)
    except:
        return ''