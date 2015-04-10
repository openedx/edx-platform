"""
Module with code executed during Studio startup
"""

import logging
from django.conf import settings

# Force settings to run so that the python path is modified
settings.INSTALLED_APPS  # pylint: disable=W0104

from django_startup import autostartup
from edx_notifications import startup
from monkey_patch import django_utils_translation

from course_groups.scope_resolver import CourseGroupScopeResolver
from student.scope_resolver import CourseEnrollmentsScopeResolver, StudentEmailScopeResolver
from projects.scope_resolver import GroupProjectParticipantsScopeResolver
from edx_notifications.scopes import register_user_scope_resolver

log = logging.getLogger(__name__)


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


def startup_notification_subsystem():
    """
    Initialize the Notification subsystem
    """
    try:
        startup.initialize()

        # register the two scope resolvers that the LMS will be providing
        # to edx-notifications
        register_user_scope_resolver('course_enrollments', CourseEnrollmentsScopeResolver())
        register_user_scope_resolver('course_group', CourseGroupScopeResolver())
        register_user_scope_resolver('group_project_participants', GroupProjectParticipantsScopeResolver())
        register_user_scope_resolver('group_project_workgroup', GroupProjectParticipantsScopeResolver())
        register_user_scope_resolver('student_email_resolver', StudentEmailScopeResolver())
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
