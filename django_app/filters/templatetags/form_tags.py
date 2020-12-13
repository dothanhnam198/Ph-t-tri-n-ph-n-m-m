from django import template
from django.contrib.admin.views.main import SEARCH_VAR

register = template.Library()


@register.inclusion_tag('IV_PhamNhan/advanced_search_form.html', takes_context=True)
def IV_PhamNhan_advance_search_form(context, cl):
    return {
        'cl': cl,
        'show_result_count': cl.result_count != cl.full_result_count,
        'search_var': SEARCH_VAR
    }