"""
Module with code executed during Studio startup
"""

from django.conf import settings

# Force settings to run so that the python path is modified
settings.INSTALLED_APPS  # pylint: disable=W0104

from django_startup import autostartup
from monkey_patch import django_utils_translation


def run():
    """
    Executed during django startup
    """
    # Patch the xml libs.
    from safe_lxml import defuse_xml_libs
    defuse_xml_libs()

    django_utils_translation.patch()

    autostartup()

    add_mimetypes()


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
