"""
Module for code that should run during LMS startup
"""

import logging

import django
from django.conf import settings

# Force settings to run so that the python path is modified

settings.INSTALLED_APPS  # pylint: disable=pointless-statement

from openedx.core.lib.django_startup import autostartup
from openedx.core.release import doc_version

from openedx.core.djangoapps.monkey_patch import django_db_models_options

import xmodule.x_module
import lms_xblock.runtime

from startup_configurations.validate_config import validate_lms_config

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

    # In order to allow modules to use a handler url, we need to
    # monkey-patch the x_module library.
    # TODO: Remove this code when Runtimes are no longer created by modulestores
    # https://openedx.atlassian.net/wiki/display/PLAT/Convert+from+Storage-centric+runtimes+to+Application-centric+runtimes
    xmodule.x_module.descriptor_global_handler_url = lms_xblock.runtime.handler_url
    xmodule.x_module.descriptor_global_local_resource_url = lms_xblock.runtime.local_resource_url

    # Set the version of docs that help-tokens will go to.
    settings.HELP_TOKENS_LANGUAGE_CODE = settings.LANGUAGE_CODE
    settings.HELP_TOKENS_VERSION = doc_version()

    # validate configurations on startup
    validate_lms_config(settings)


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
