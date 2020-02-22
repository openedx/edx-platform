"""
Exposes Django utilities for consumption in the xmodule library
NOTE: This file should only be imported into 'django-safe' code, i.e. known that this code runs int the Django
runtime environment with the djangoapps in common configured to load
"""


import webpack_loader
# NOTE: we are importing this method so that any module that imports us has access to get_current_request
from crum import get_current_request


def get_current_request_hostname():
    """
    This method will return the hostname that was used in the current Django request
    """
    hostname = None
    request = get_current_request()
    if request:
        hostname = request.META.get('HTTP_HOST')

    return hostname


def add_webpack_to_fragment(fragment, bundle_name, extension=None, config='DEFAULT'):
    """
    Add all webpack chunks to the supplied fragment as the appropriate resource type.
    """
    for chunk in webpack_loader.utils.get_files(bundle_name, extension, config):
        if chunk['name'].endswith(('.js', '.js.gz')):
            fragment.add_javascript_url(chunk['url'])
        elif chunk['name'].endswith(('.css', '.css.gz')):
            fragment.add_css_url(chunk['url'])
