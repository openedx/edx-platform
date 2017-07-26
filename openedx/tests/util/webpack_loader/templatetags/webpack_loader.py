"""
This module mocks the external package django-webpack-loader within
python unittest execution, so python tests have no dependency on
frontend assets. See LEARNER-1938 for further details.
"""
from django import template

register = template.Library()


@register.simple_tag
def render_bundle(bundle_name):
    """
    This is the only webpack_loader function we call directly.
    """
    return ''
