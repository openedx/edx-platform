"""
Module with code executed during Studio startup
"""

import logging
from django.conf import settings

# Force settings to run so that the python path is modified

settings.INSTALLED_APPS  # pylint: disable=pointless-statement

import django
from django.conf import settings

import cms.lib.xblock.runtime
import xmodule.x_module
from openedx.core.djangoapps.monkey_patch import django_db_models_options
from openedx.core.djangoapps.theming.core import enable_theming
from openedx.core.djangoapps.theming.helpers import is_comprehensive_theming_enabled
from openedx.core.lib.django_startup import autostartup
from openedx.core.lib.xblock_utils import xblock_local_resource_url
from openedx.core.release import doc_version
from startup_configurations.validate_config import validate_cms_config

# edx notifications related imports
from student.scope_resolver import CourseEnrollmentsScopeResolver, StudentEmailScopeResolver
from openedx.core.djangoapps.course_groups.scope_resolver import CourseGroupScopeResolver
from edx_solutions_projects.scope_resolver import GroupProjectParticipantsScopeResolver
from edx_notifications.scopes import register_user_scope_resolver
from edx_notifications.namespaces import register_namespace_resolver
from util.namespace_resolver import CourseNamespaceResolver
from edx_notifications import startup

log = logging.getLogger(__name__)

# edx notifications related imports
from openedx.core.djangoapps.course_groups.scope_resolver import CourseGroupScopeResolver
from student.scope_resolver import CourseEnrollmentsScopeResolver, StudentEmailScopeResolver
from edx_solutions_projects.scope_resolver import GroupProjectParticipantsScopeResolver
from edx_notifications.scopes import register_user_scope_resolver
from edx_notifications.namespaces import register_namespace_resolver
from util.namespace_resolver import CourseNamespaceResolver
from edx_notifications import startup

log = logging.getLogger(__name__)


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

    if settings.FEATURES.get('ENABLE_NOTIFICATIONS', False):
        startup_notification_subsystem()

    if settings.FEATURES.get('EDX_SOLUTIONS_API', False) and \
            settings.FEATURES.get('DISABLE_SOLUTIONS_APPS_SIGNALS', False):
        disable_solutions_apps_signals()

    # In order to allow descriptors to use a handler url, we need to
    # monkey-patch the x_module library.
    # TODO: Remove this code when Runtimes are no longer created by modulestores
    # https://openedx.atlassian.net/wiki/display/PLAT/Convert+from+Storage-centric+runtimes+to+Application-centric+runtimes
    xmodule.x_module.descriptor_global_handler_url = cms.lib.xblock.runtime.handler_url
    xmodule.x_module.descriptor_global_local_resource_url = xblock_local_resource_url

    # Set the version of docs that help-tokens will go to.
    settings.HELP_TOKENS_LANGUAGE_CODE = settings.LANGUAGE_CODE
    settings.HELP_TOKENS_VERSION = doc_version()

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


def disable_solutions_apps_signals():
    """
    Disables signals receivers in solutions apps
    """
    from edx_solutions_api_integration.test_utils import SignalDisconnectTestMixin
    SignalDisconnectTestMixin.disconnect_signals()


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
