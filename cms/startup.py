"""
Module with code executed during Studio startup
"""

from django.conf import settings

# Force settings to run so that the python path is modified

settings.INSTALLED_APPS  # pylint: disable=pointless-statement

from openedx.core.lib.django_startup import autostartup
import django
from openedx.core.djangoapps.monkey_patch import django_db_models_options
from openedx.core.lib.xblock_utils import xblock_local_resource_url

import xmodule.x_module
import cms.lib.xblock.runtime

from startup_configurations.validate_config import validate_cms_config
from openedx.core.djangoapps.theming.core import enable_theming
from openedx.core.djangoapps.theming.helpers import is_comprehensive_theming_enabled


def run():
    """
    Executed during django startup
    """
    django_db_models_options.patch()

    # Comprehensive theming needs to be set up before django startup,
    # because modifying django template paths after startup has no effect.
    if is_comprehensive_theming_enabled():
        enable_theming()

    django.setup()

    autostartup()

    add_mimetypes()

    # In order to allow descriptors to use a handler url, we need to
    # monkey-patch the x_module library.
    # TODO: Remove this code when Runtimes are no longer created by modulestores
    # https://openedx.atlassian.net/wiki/display/PLAT/Convert+from+Storage-centric+runtimes+to+Application-centric+runtimes
    xmodule.x_module.descriptor_global_handler_url = cms.lib.xblock.runtime.handler_url
    xmodule.x_module.descriptor_global_local_resource_url = xblock_local_resource_url

    # validate configurations on startup
    validate_cms_config(settings)


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
