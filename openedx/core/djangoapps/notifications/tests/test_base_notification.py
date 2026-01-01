"""
Tests for base_notification
"""
from openedx.core.djangoapps.notifications import base_notification
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase


class NotificationPreferenceValidationTest(ModuleStoreTestCase):
    """
    Tests to validate if notification preference constants are valid
    """

    def test_validate_notification_apps(self):
        """
        Tests if COURSE_NOTIFICATION_APPS constant has all required keys with valid
        data type for new notification app
        """
        bool_keys = ['enabled', 'core_web', 'core_push', 'core_email']
        notification_apps = base_notification.COURSE_NOTIFICATION_APPS
        assert "" not in notification_apps
        for app_data in notification_apps.values():
            assert 'core_info' in app_data.keys()
            assert isinstance(app_data['non_editable'], list)
            assert isinstance(app_data['core_email_cadence'], str)
            for key in bool_keys:
                assert isinstance(app_data[key], bool)

    def test_validate_core_notification_types(self):
        """
        Tests if COURSE_NOTIFICATION_TYPES constant has all required keys with valid
        data type for core notification type
        """
        str_keys = ['notification_app', 'name', 'email_template']
        notification_types = base_notification.COURSE_NOTIFICATION_TYPES
        assert "" not in notification_types
        for notification_type in notification_types.values():
            if not notification_type['is_core']:
                continue
            assert isinstance(notification_type['is_core'], bool)
            assert isinstance(notification_type['content_context'], dict)
            assert 'content_template' in notification_type.keys()
            for key in str_keys:
                assert isinstance(notification_type[key], str)

    def test_validate_non_core_notification_types(self):
        """
        Tests if COURSE_NOTIFICATION_TYPES constant has all required keys with valid
        data type for non-core notification type
        """
        str_keys = ['notification_app', 'name', 'info', 'email_template']
        bool_keys = ['is_core', 'web', 'email', 'push']
        notification_types = base_notification.COURSE_NOTIFICATION_TYPES
        assert "" not in notification_types
        for notification_type in notification_types.values():
            if notification_type['is_core']:
                continue
            assert 'content_template' in notification_type.keys()
            assert isinstance(notification_type['content_context'], dict)
            assert isinstance(notification_type['non_editable'], list)
            assert isinstance(notification_type['email_cadence'], str)
            for key in str_keys:
                assert isinstance(notification_type[key], str)
            for key in bool_keys:
                assert isinstance(notification_type[key], bool)
