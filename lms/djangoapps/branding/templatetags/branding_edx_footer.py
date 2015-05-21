"""Branding app Django template tag for rendering the footer. """
from django import template
from django.core.urlresolvers import reverse
from branding import api as branding_api


register = template.Library()  # pylint:disable=invalid-name


@register.simple_tag(takes_context=True)
def branding_edx_footer(context):
    """Render the branded EdX footer in a Django template.

    Use this template tag in Django templates to render the
    branded EdX version of the footer.  This uses the same mechanism
    as external sites that include the footer (e.g. the marketing site
    and blog), ensuring that the footers are consistent.
    """
    is_secure = context['request'].is_secure()
    return (
        '<div id="edx-branding-footer" data-base-url="{base_url}"></div>'
        '<script type="text/javascript" src="{js_url}"></script>'
    ).format(
        base_url=branding_api.get_base_url(is_secure=is_secure),
        js_url=reverse('branding_footer_ext', kwargs={'extension': 'js'}),
    )
