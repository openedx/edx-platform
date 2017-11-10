"""
File to support the startup of the Notification subsystem. This should be called
at least once at the beginning of any process lifecycle
"""

from edx_notifications.signals import perform_type_registrations, perform_timer_registrations

# we need to import the standard notification type registrations so that they can hook in
# in their signal receivers
from edx_notifications.openedx import notification_type_registration  # pylint: disable=unused-import
from edx_notifications.digests import register_digest_timers, create_default_notification_preferences  # pylint: disable=unused-import
from edx_notifications.timer import register_purge_notifications_timer  # pylint: disable=unused-import

from edx_notifications.scopes import register_user_scope_resolver, SingleUserScopeResolver

from edx_notifications.namespaces import DefaultNotificationNamespaceResolver, register_namespace_resolver

# This is unfortunate, but to have the standard Open edX
# NotificationTypes get registered on startup we have
# to import the modules, otherwise, they will
# not register their Django signal receivers


def initialize(namespace_resolver=None, register_system_types=True):
    """
    Startup entry point for the Notification subsystem
    """

    # alert the application tiers that they should register their
    # notification types, but this optional (default=True)
    if register_system_types:
        perform_type_registrations.send(sender=None)

    # alert the application tiers that they should register their
    # notification timers/callbacks
    perform_timer_registrations.send(sender=None)

    # install the system-defined Notification Preferences
    create_default_notification_preferences()

    register_user_scope_resolver('user', SingleUserScopeResolver(), {})

    if not namespace_resolver:
        namespace_resolver = DefaultNotificationNamespaceResolver()

    register_namespace_resolver(namespace_resolver, None)
