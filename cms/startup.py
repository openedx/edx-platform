"""
Module with code executed during Studio startup
"""

from django.conf import settings

# Force settings to run so that the python path is modified
settings.INSTALLED_APPS  # pylint: disable=pointless-statement

from openedx.core.lib.django_startup import autostartup
import django
from monkey_patch import (
    third_party_auth,
    django_db_models_options,
    collectstatic
)
from openedx.core.lib.xblock_utils import xblock_local_resource_url

import xmodule.x_module
import cms.lib.xblock.runtime

from openedx.core.djangoapps.theming.core import enable_comprehensive_theme


def run():
    """
    Executed during django startup
    """
    third_party_auth.patch()
    django_db_models_options.patch()
    collectstatic.patch()

    # Comprehensive theming needs to be set up before django startup,
    # because modifying django template paths after startup has no effect.
    if settings.COMPREHENSIVE_THEME_DIR:
        enable_comprehensive_theme(settings.COMPREHENSIVE_THEME_DIR)

    django.setup()

    autostartup()

    add_mimetypes()

    if settings.FEATURES.get('USE_CUSTOM_THEME', False):
        enable_theme()

    # In order to allow descriptors to use a handler url, we need to
    # monkey-patch the x_module library.
    # TODO: Remove this code when Runtimes are no longer created by modulestores
    # https://openedx.atlassian.net/wiki/display/PLAT/Convert+from+Storage-centric+runtimes+to+Application-centric+runtimes
    xmodule.x_module.descriptor_global_handler_url = cms.lib.xblock.runtime.handler_url
    xmodule.x_module.descriptor_global_local_resource_url = xblock_local_resource_url


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


def enable_theme():
    """
    Enable the settings for a custom theme, whose files should be stored
    in ENV_ROOT/themes/THEME_NAME (e.g., edx_all/themes/stanford).
    At this moment this is actually just a fix for collectstatic,
    (see https://openedx.atlassian.net/browse/TNL-726),
    but can be improved with a full theming option also for Studio
    in the future (see lms.startup)
    """
    # Workaround for setting THEME_NAME to an empty
    # string which is the default due to this ansible
    # bug: https://github.com/ansible/ansible/issues/4812
    if settings.THEME_NAME == "":
        settings.THEME_NAME = None
        return

    assert settings.FEATURES['USE_CUSTOM_THEME']
    settings.FAVICON_PATH = 'themes/{name}/images/favicon.ico'.format(
        name=settings.THEME_NAME
    )

    # Calculate the location of the theme's files
    theme_root = settings.ENV_ROOT / "themes" / settings.THEME_NAME

    # Namespace the theme's static files to 'themes/<theme_name>' to
    # avoid collisions with default edX static files
    settings.STATICFILES_DIRS.append(
        (u'themes/{}'.format(settings.THEME_NAME), theme_root / 'static')
    )
