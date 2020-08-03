from django import template
from django.template.loader import get_template

register = template.Library()


@register.simple_tag(takes_context=True)
def sso_meta(context):
    return get_template('features/specializations/sso_meta_template.html').render(context.flatten())
