"""
Base setup for Notification Apps and Types.
"""
from typing import Dict

COURSE_NOTIFICATION_TYPES = {
    'new_comment_on_response': {
        'notification_app': 'discussion',
        'name': 'new_comment_on_response',
        'is_core': True,
        'info': 'Comment on response',
        'content_template': '<p><strong>{replier_name}</strong> replied on your response in '
                            '<strong>{post_title}</strong></p>',
        'content_context': {
            'post_title': 'Post title',
            'replier_name': 'replier name',
        },
        'email_template': '',
    },
    'new_comment': {
        'notification_app': 'discussion',
        'name': 'new_comment',
        'is_core': False,
        'web': True,
        'email': True,
        'push': True,
        'info': 'Comment on post',
        'non-editable': ['web', 'email'],
        'content_template': '<p><strong>{replier_name}</strong> replied on <strong>{author_name}</strong> response '
                            'to your post <strong>{post_title}</strong></p>',
        'content_context': {
            'post_title': 'Post title',
            'author_name': 'author name',
            'replier_name': 'replier name',
        },
        'email_template': '',
    },
    'new_response': {
        'notification_app': 'discussion',
        'name': 'new_response',
        'is_core': False,
        'web': True,
        'email': True,
        'push': True,
        'info': 'Response on post',
        'non-editable': [],
        'content_template': '<p><strong>{replier_name}</strong> responded to your '
                            'post <strong>{post_title}</strong></p>',
        'content_context': {
            'post_title': 'Post title',
            'replier_name': 'replier name',
        },
        'email_template': '',
    },
}

COURSE_NOTIFICATION_APPS = {
    'discussion': {
        'enabled': True,
        'core_info': '',
        'core_web': True,
        'core_email': True,
        'core_push': True,
    }
}


class NotificationTypeManager:
    """
    Manager for notification types
    """
    notification_types: Dict = {}

    def __init__(self):
        self.notification_types = COURSE_NOTIFICATION_TYPES

    def get_notification_types_by_app(self, notification_app):
        """
        Returns notification types for the given notification app.
        """
        return [
            notification_type for _, notification_type in self.notification_types.items()
            if notification_type.get('notification_app', None) == notification_app
        ]

    def get_core_and_non_core_notification_types(self, notification_app):
        """
        Returns core notification types for the given app name.
        """
        notification_types = self.get_notification_types_by_app(notification_app)
        core_notification_types = []
        non_core_notification_types = []
        for notification_type in notification_types:
            if notification_type.get('is_core', None):
                core_notification_types.append(notification_type)
            else:
                non_core_notification_types.append(notification_type)
        return core_notification_types, non_core_notification_types

    @staticmethod
    def get_non_editable_notification_channels(notification_types):
        """
        Returns non-editable notification channels for the given notification types.
        """
        non_editable_notification_channels = {}
        for notification_type in notification_types:
            if notification_type.get('non-editable', None):
                non_editable_notification_channels[notification_type.get('name')] = \
                    notification_type.get('non-editable')
        return non_editable_notification_channels

    @staticmethod
    def get_non_core_notification_type_preferences(non_core_notification_types):
        """
        Returns non-core notification type preferences for the given notification types.
        """
        non_core_notification_type_preferences = {}
        for notification_type in non_core_notification_types:
            non_core_notification_type_preferences[notification_type.get('name')] = {
                'web': notification_type.get('web', False),
                'email': notification_type.get('email', False),
                'push': notification_type.get('push', False),
                'info': notification_type.get('info', ''),
            }
        return non_core_notification_type_preferences

    def get_notification_app_preference(self, notification_app):
        """
        Returns notification app preferences for the given notification app.
        """
        core_notification_types, non_core_notification_types = self.get_core_and_non_core_notification_types(
            notification_app,
        )
        non_core_notification_types_preferences = self.get_non_core_notification_type_preferences(
            non_core_notification_types,
        )
        non_editable_notification_channels = self.get_non_editable_notification_channels(non_core_notification_types)
        core_notification_types_name = [notification_type.get('name') for notification_type in core_notification_types]
        return non_core_notification_types_preferences, core_notification_types_name, non_editable_notification_channels


class NotificationAppManager:
    """
    Notification app manager
    """
    notification_apps: Dict = {}

    def __init__(self):
        self.notification_apps = COURSE_NOTIFICATION_APPS

    def add_core_notification_preference(self, notification_app_attrs, notification_types):
        """
        Adds core notification preference for the given notification app.
        """
        notification_types['core'] = {
            'web': notification_app_attrs.get('core_web', False),
            'email': notification_app_attrs.get('core_email', False),
            'push': notification_app_attrs.get('core_push', False),
            'info': notification_app_attrs.get('core_info', ''),
        }

    def get_notification_app_preferences(self):
        """
        Returns notification app preferences for the given name.
        """
        course_notification_preference_config = {}
        for notification_app_key, notification_app_attrs in COURSE_NOTIFICATION_APPS.items():
            notification_app_preferences = {}
            notification_types, core_notifications, \
                non_editable_channels = NotificationTypeManager().get_notification_app_preference(notification_app_key)
            self.add_core_notification_preference(notification_app_attrs, notification_types)

            notification_app_preferences['enabled'] = notification_app_attrs.get('enabled', False)
            notification_app_preferences['core_notification_types'] = core_notifications
            notification_app_preferences['notification_types'] = notification_types
            notification_app_preferences['non_editable'] = non_editable_channels
            course_notification_preference_config[notification_app_key] = notification_app_preferences

            return course_notification_preference_config
        return None
