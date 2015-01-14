"""
Module with code executed during Studio startup
"""

from django.conf import settings

# Force settings to run so that the python path is modified
settings.INSTALLED_APPS  # pylint: disable=W0104

from django_startup import autostartup
from monkey_patch import django_utils_translation
from util import keyword_substitution
from lms.startup import get_keyword_function_map


def run():
    """
    Executed during django startup
    """
    django_utils_translation.patch()

    autostartup()

    add_mimetypes()

    # Monkey patch the keyword function map
    if keyword_substitution.keyword_function_map_is_empty():
        keyword_substitution.add_keyword_function_map(get_keyword_function_map())
        # Once keyword function map is set, make update function do nothing
        keyword_substitution.add_keyword_function_map = lambda x: None

def add_mimetypes():
    """
    Add extra mimetypes. Used in xblock_resource.

    If you add a mimetype here, be sure to also add it in lms/startup.py.
    """
    import mimetypes

    mimetypes.add_type('application/vnd.ms-fontobject', '.eot')
    mimetypes.add_type('application/x-font-opentype', '.otf')
    mimetypes.add_type('application/x-font-ttf', '.ttf')
    mimetypes.add_type('application/font-woff', '.woff')
