"""
Module with code executed during Studio startup
"""

import logging
from django.conf import settings

# Force settings to run so that the python path is modified
settings.INSTALLED_APPS  # pylint: disable=pointless-statement

from openedx.core.lib.django_startup import autostartup

from edx_notifications import startup
from monkey_patch import django_utils_translation

from openedx.core.djangoapps.course_groups.scope_resolver import CourseGroupScopeResolver
from student.scope_resolver import CourseEnrollmentsScopeResolver, StudentEmailScopeResolver
from projects.scope_resolver import GroupProjectParticipantsScopeResolver
from edx_notifications.scopes import register_user_scope_resolver
from edx_notifications.namespaces import register_namespace_resolver
from util.namespace_resolver import CourseNamespaceResolver

log = logging.getLogger(__name__)


def run():
    """
    Executed during django startup
    """
    django_utils_translation.patch()

    autostartup()

    add_mimetypes()

    if settings.FEATURES.get('USE_CUSTOM_THEME', False):
        enable_theme()
    if settings.FEATURES.get('ENABLE_NOTIFICATIONS', False):
        startup_notification_subsystem()


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


def startup_notification_subsystem():
    """
    Initialize the Notification subsystem
    """
    try:
        startup.initialize()

        # register the scope resolvers that the runtime will be providing
        # to edx-notifications
        register_user_scope_resolver('course_enrollments', CourseEnrollmentsScopeResolver())
        register_user_scope_resolver('course_group', CourseGroupScopeResolver())
        register_user_scope_resolver('group_project_participants', GroupProjectParticipantsScopeResolver())
        register_user_scope_resolver('group_project_workgroup', GroupProjectParticipantsScopeResolver())
        register_user_scope_resolver('student_email_resolver', StudentEmailScopeResolver())

        # register namespace resolver
        register_namespace_resolver(CourseNamespaceResolver())
    except Exception, ex:
        # Note this will fail when we try to run migrations as manage.py will call startup.py
        # and startup.initialze() will try to manipulate some database tables.
        # We need to research how to identify when we are being started up as part of
        # a migration script
        log.error(
            'There was a problem initializing notifications subsystem. '
            'This could be because the database tables have not yet been created and '
            './manage.py lms syncdb needs to run setup.py. Error was "{err_msg}". Continuing...'.format(err_msg=str(ex))
        )
