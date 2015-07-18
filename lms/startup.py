"""
Module for code that should run during LMS startup
"""

# pylint: disable=unused-argument

from django.conf import settings

# Force settings to run so that the python path is modified
settings.INSTALLED_APPS  # pylint: disable=pointless-statement

from openedx.core.lib.django_startup import autostartup
import edxmako
import logging
from monkey_patch import django_utils_translation
import analytics


from microsite_configuration import microsite

log = logging.getLogger(__name__)


def run():
    """
    Executed during django startup
    """
    django_utils_translation.patch()

    autostartup()

    add_mimetypes()

    if settings.FEATURES.get('USE_CUSTOM_THEME', False):
        enable_stanford_theme()

    if settings.FEATURES.get('USE_MICROSITES', False):
        microsite.enable_microsites(log)

    if settings.FEATURES.get('ENABLE_THIRD_PARTY_AUTH', False):
        enable_third_party_auth()

    # Initialize Segment analytics module by setting the write_key.
    if settings.LMS_SEGMENT_KEY:
        analytics.write_key = settings.LMS_SEGMENT_KEY

    # register any dependency injections that we need to support in edx_proctoring
    # right now edx_proctoring is dependent on the openedx.core.djangoapps.credit
    # as well as the instructor dashboard (for deleting student attempts)
    if settings.FEATURES.get('ENABLE_PROCTORED_EXAMS'):
        # Import these here to avoid circular dependencies of the form:
        # edx-platform app --> DRF --> django translation --> edx-platform app
        from edx_proctoring.runtime import set_runtime_service
        from instructor.services import InstructorService
        from openedx.core.djangoapps.credit.services import CreditService
        set_runtime_service('credit', CreditService())
        set_runtime_service('instructor', InstructorService())


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
    settings.TEMPLATE_DIRS.insert(0, theme_root / 'templates')
    edxmako.paths.add_lookup('main', theme_root / 'templates', prepend=True)

    # Namespace the theme's static files to 'themes/<theme_name>' to
    # avoid collisions with default edX static files
    settings.STATICFILES_DIRS.append(
        (u'themes/{}'.format(settings.THEME_NAME), theme_root / 'static')
    )

    # Include theme locale path for django translations lookup
    settings.LOCALE_PATHS = (theme_root / 'conf/locale',) + settings.LOCALE_PATHS


def enable_third_party_auth():
    """
    Enable the use of third_party_auth, which allows users to sign in to edX
    using other identity providers. For configuration details, see
    common/djangoapps/third_party_auth/settings.py.
    """

    from third_party_auth import settings as auth_settings
    auth_settings.apply_settings(settings)
