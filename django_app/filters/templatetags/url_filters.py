from django import template

register = template.Library()


@register.filter(name='get_menu_class')
def get_menu_class(app, path):
    for model in app['items']:
        if model['url'] == path:
            return 'menu-open'
    return ''
