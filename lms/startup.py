"""
Module for code that should run during LMS startup
"""

import logging

import django
from django.conf import settings

# Force settings to run so that the python path is modified

settings.INSTALLED_APPS  # pylint: disable=pointless-statement

from openedx.core.lib.django_startup import autostartup

from openedx.core.djangoapps.monkey_patch import django_db_models_options

log = logging.getLogger(__name__)


def run():
    """
    Executed during django startup

    NOTE: DO **NOT** add additional code to this method or this file! The Platform Team
          is moving all startup code to more standard locations using Django best practices.
    """
    django_db_models_options.patch()

    django.setup()

    autostartup()

    add_mimetypes()


def add_mimetypes():
    """
    Add extra mimetypes. Used in xblock_resource.

    If you add a mimetype here, be sure to also add it in cms/startup.py.
    """
    import mimetypes

    mimetypes.add_type('application/vnd.ms-fontobject', '.eot')
    mimetypes.add_type('application/x-font-opentype', '.otf')
    mimetypes.add_type('application/x-font-ttf', '.ttf')
    mimetypes.add_type('application/font-woff', '.woff')
