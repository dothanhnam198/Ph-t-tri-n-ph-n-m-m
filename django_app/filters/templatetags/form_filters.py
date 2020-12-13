from django import template

register = template.Library()


@register.filter(name='get_quick_search_param')
def get_quick_search_param(value):
    return value.split(',,')[0]


@register.filter(name='get_advance_search_param')
def get_advance_search_param(value, name):
    params = value.split(',,')
    for i in range(len(params)):
        if i > 0:
            param = params[i].split('=')
            if param[0] == name:
                return param[1]

    return ''
