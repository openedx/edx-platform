"""
Module for code that should run during LMS startup
"""

import django
from django.conf import settings

# Force settings to run so that the python path is modified
settings.INSTALLED_APPS  # pylint: disable=pointless-statement

from openedx.core.lib.django_startup import autostartup
import edxmako
import logging
import analytics
from monkey_patch import third_party_auth


import xmodule.x_module
import lms_xblock.runtime

log = logging.getLogger(__name__)


def run():
    """
    Executed during django startup
    """
    third_party_auth.patch()

    # To override the settings before executing the autostartup() for python-social-auth
    if settings.FEATURES.get('ENABLE_THIRD_PARTY_AUTH', False):
        enable_third_party_auth()

    django.setup()

    autostartup()

    add_mimetypes()

    if settings.FEATURES.get('USE_CUSTOM_THEME', False):
        enable_stanford_theme()

    if settings.FEATURES.get('USE_MICROSITES', False):
        enable_microsites()

    # Initialize Segment analytics module by setting the write_key.
    if settings.LMS_SEGMENT_KEY:
        analytics.write_key = settings.LMS_SEGMENT_KEY

    # register any dependency injections that we need to support in edx_proctoring
    # right now edx_proctoring is dependent on the openedx.core.djangoapps.credit
    if settings.FEATURES.get('ENABLE_SPECIAL_EXAMS'):
        # Import these here to avoid circular dependencies of the form:
        # edx-platform app --> DRF --> django translation --> edx-platform app
        from edx_proctoring.runtime import set_runtime_service
        from instructor.services import InstructorService
        from openedx.core.djangoapps.credit.services import CreditService
        set_runtime_service('credit', CreditService())

        # register InstructorService (for deleting student attempts and user staff access roles)
        set_runtime_service('instructor', InstructorService())

    # In order to allow modules to use a handler url, we need to
    # monkey-patch the x_module library.
    # TODO: Remove this code when Runtimes are no longer created by modulestores
    # https://openedx.atlassian.net/wiki/display/PLAT/Convert+from+Storage-centric+runtimes+to+Application-centric+runtimes
    xmodule.x_module.descriptor_global_handler_url = lms_xblock.runtime.handler_url
    xmodule.x_module.descriptor_global_local_resource_url = lms_xblock.runtime.local_resource_url


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


def enable_stanford_theme():
    """
    Enable the settings for a custom theme, whose files should be stored
    in ENV_ROOT/themes/THEME_NAME (e.g., edx_all/themes/stanford).
    """
    # Workaround for setting THEME_NAME to an empty
    # string which is the default due to this ansible
    # bug: https://github.com/ansible/ansible/issues/4812
    if getattr(settings, "THEME_NAME", "") == "":
        settings.THEME_NAME = None
        return

    assert settings.FEATURES['USE_CUSTOM_THEME']
    settings.FAVICON_PATH = 'themes/{name}/images/favicon.ico'.format(
        name=settings.THEME_NAME
    )

    # Calculate the location of the theme's files
    theme_root = settings.ENV_ROOT / "themes" / settings.THEME_NAME

    # Include the theme's templates in the template search paths
    settings.DEFAULT_TEMPLATE_ENGINE['DIRS'].insert(0, theme_root / 'templates')
    edxmako.paths.add_lookup('main', theme_root / 'templates', prepend=True)

    # Namespace the theme's static files to 'themes/<theme_name>' to
    # avoid collisions with default edX static files
    settings.STATICFILES_DIRS.append(
        (u'themes/{}'.format(settings.THEME_NAME), theme_root / 'static')
    )

    # Include theme locale path for django translations lookup
    settings.LOCALE_PATHS = (theme_root / 'conf/locale',) + settings.LOCALE_PATHS


def enable_microsites():
    """
    Enable the use of microsites, which are websites that allow
    for subdomains for the edX platform, e.g. foo.edx.org
    """

    microsites_root = settings.MICROSITE_ROOT_DIR
    microsite_config_dict = settings.MICROSITE_CONFIGURATION

    for ms_name, ms_config in microsite_config_dict.items():
        # Calculate the location of the microsite's files
        ms_root = microsites_root / ms_name
        ms_config = microsite_config_dict[ms_name]

        # pull in configuration information from each
        # microsite root

        if ms_root.isdir():
            # store the path on disk for later use
            ms_config['microsite_root'] = ms_root

            template_dir = ms_root / 'templates'
            ms_config['template_dir'] = template_dir

            ms_config['microsite_name'] = ms_name
            log.info('Loading microsite %s', ms_root)
        else:
            # not sure if we have application logging at this stage of
            # startup
            log.error('Error loading microsite %s. Directory does not exist', ms_root)
            # remove from our configuration as it is not valid
            del microsite_config_dict[ms_name]

    # if we have any valid microsites defined, let's wire in the Mako and STATIC_FILES search paths
    if microsite_config_dict:
        settings.DEFAULT_TEMPLATE_ENGINE['DIRS'].append(microsites_root)
        edxmako.paths.add_lookup('main', microsites_root)

        settings.STATICFILES_DIRS.insert(0, microsites_root)


def enable_third_party_auth():
    """
    Enable the use of third_party_auth, which allows users to sign in to edX
    using other identity providers. For configuration details, see
    common/djangoapps/third_party_auth/settings.py.
    """

    from third_party_auth import settings as auth_settings
    auth_settings.apply_settings(settings)
