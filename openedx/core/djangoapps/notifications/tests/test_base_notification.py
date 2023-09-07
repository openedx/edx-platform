"""
Tests for base_notification
"""
from common.djangoapps.student.tests.factories import UserFactory
from openedx.core.djangoapps.notifications import base_notification, models
from openedx.core.djangoapps.notifications.models import (
    CourseNotificationPreference,
    get_course_notification_preference_config_version
)
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


class NotificationPreferenceSyncManagerTest(ModuleStoreTestCase):
    """
    Tests NotificationPreferenceSyncManager
    """

    @classmethod
    def setUpClass(cls):
        """
        Overriding this method to save current config
        """
        super(NotificationPreferenceSyncManagerTest, cls).setUpClass()
        cls.current_apps = base_notification.COURSE_NOTIFICATION_APPS
        cls.current_types = base_notification.COURSE_NOTIFICATION_TYPES
        cls.current_config_version = models.COURSE_NOTIFICATION_CONFIG_VERSION

    @classmethod
    def tearDownClass(cls):
        """
        Overriding this method to restore saved config
        """
        super(NotificationPreferenceSyncManagerTest, cls).tearDownClass()
        base_notification.COURSE_NOTIFICATION_APPS = cls.current_apps
        base_notification.COURSE_NOTIFICATION_TYPES = cls.current_types
        models.COURSE_NOTIFICATION_CONFIG_VERSION = cls.current_config_version

    def setUp(self):
        """
        Setup test cases
        """
        super().setUp()
        self.user = UserFactory()
        self.course = CourseFactory.create(
            org='testorg',
            number='testcourse',
            run='testrun'
        )
        self.default_app_name = "default_app"
        self.default_app_value = self._create_notification_app()
        self.default_type_name = "default_type"
        self.default_type_value = self._create_notification_type(self.default_type_name)
        self._set_course_notification_apps({self.default_app_name: self.default_app_value})
        self._set_course_notification_types({self.default_type_name: self.default_type_value})
        self._set_notification_config_version(1)
        self.preference = CourseNotificationPreference(
            user=self.user,
            course_id=self.course.id,
        )

    def _set_course_notification_apps(self, apps):
        """
        Set COURSE_NOTIFICATION_APPS
        """
        base_notification.COURSE_NOTIFICATION_APPS = apps

    def _set_course_notification_types(self, notifications_types):
        """
        Set COURSE_NOTIFICATION_TYPES
        """
        base_notification.COURSE_NOTIFICATION_TYPES = notifications_types

    def _set_notification_config_version(self, config_version):
        """
        Set COURSE_NOTIFICATION_CONFIG_VERSION
        """

        models.COURSE_NOTIFICATION_CONFIG_VERSION = config_version

    def _create_notification_app(self, overrides=None):
        """
        Create a notification app
        """
        notification_app = {
            'enabled': True,
            'core_info': '',
            'core_web': True,
            'core_email': True,
            'core_push': True,
        }
        if overrides is not None:
            notification_app.update(overrides)
        return notification_app

    def _create_notification_type(self, name, overrides=None):
        """
        Creates a new notification type
        """
        notification_type = {
            'notification_app': self.default_app_name,
            'name': name,
            'is_core': False,
            'web': True,
            'email': True,
            'push': True,
            'info': '',
            'non_editable': [],
            'content_template': '',
            'content_context': {},
            'email_template': '',
        }
        if overrides is not None:
            notification_type.update(overrides)
        return notification_type

    def test_app_addition_and_removal(self):
        """
        Tests if new app is added/removed in existing preference
        """
        current_config_version = get_course_notification_preference_config_version()
        app_name = 'discussion'
        new_app_value = self._create_notification_app()
        self._set_notification_config_version(current_config_version + 1)
        self._set_course_notification_apps({app_name: new_app_value})
        new_config = CourseNotificationPreference.get_updated_user_course_preferences(self.user, self.course.id)
        assert self.default_app_name not in new_config.notification_preference_config
        assert app_name in new_config.notification_preference_config

    def test_app_toggle_value_persist(self):
        """
        Tests if app toggle value persists even if default is changed
        """
        enabled_value = self.default_app_value['enabled']
        config = CourseNotificationPreference.get_updated_user_course_preferences(self.user, self.course.id)
        assert config.notification_preference_config[self.default_app_name]['enabled'] == enabled_value
        base_notification.COURSE_NOTIFICATION_APPS[self.default_app_name]['enabled'] = not enabled_value
        current_config_version = get_course_notification_preference_config_version()
        self._set_notification_config_version(current_config_version + 1)
        new_config = CourseNotificationPreference.get_updated_user_course_preferences(self.user, self.course.id)
        assert new_config.config_version == current_config_version + 1
        assert new_config.notification_preference_config[self.default_app_name]['enabled'] == enabled_value

    def test_notification_type_addition_and_removal(self):
        """
        Test if new notification type is added/removed in existing preferences
        """
        current_config_version = get_course_notification_preference_config_version()
        type_name = 'new_type'
        new_type_value = self._create_notification_type(type_name)
        self._set_notification_config_version(current_config_version + 1)
        self._set_course_notification_types({
            type_name: new_type_value
        })
        preferences = CourseNotificationPreference.get_updated_user_course_preferences(self.user, self.course.id)
        new_config = preferences.notification_preference_config
        assert type_name in new_config[self.default_app_name]['notification_types']
        assert self.default_type_name not in new_config[self.default_app_name]['notification_types']

    def test_notification_type_toggle_value_persist(self):
        """
        Tests if notification type value persists if default is changed
        """
        config = CourseNotificationPreference.get_updated_user_course_preferences(self.user, self.course.id)
        preferences = config.notification_preference_config
        preference_type = preferences[self.default_app_name]['notification_types'][self.default_type_name]
        web_value = preference_type['web']
        email_value = preference_type['email']
        push_value = preference_type['push']

        base_notification.COURSE_NOTIFICATION_TYPES[self.default_type_name].update({
            'web': not web_value,
            'email': not email_value,
            'push': not push_value,
        })
        current_config_version = get_course_notification_preference_config_version()
        self._set_notification_config_version(current_config_version + 1)

        new_config = CourseNotificationPreference.get_updated_user_course_preferences(self.user, self.course.id)
        preferences = new_config.notification_preference_config
        preference_type = preferences[self.default_app_name]['notification_types'][self.default_type_name]
        assert new_config.config_version == current_config_version + 1
        assert preference_type['web'] == web_value
        assert preference_type['email'] == email_value
        assert preference_type['push'] == push_value

    def test_non_editable_addition_and_removal(self):
        """
        Tests if non_editable updates on existing preferences
        """
        current_config_version = get_course_notification_preference_config_version()
        base_notification.COURSE_NOTIFICATION_TYPES[self.default_type_name]['non_editable'] = ['web']
        self._set_notification_config_version(current_config_version + 1)
        new_config = CourseNotificationPreference.get_updated_user_course_preferences(self.user, self.course.id)
        preferences = new_config.notification_preference_config
        preference_non_editable = preferences[self.default_app_name]['non_editable'][self.default_type_name]
        assert 'web' in preference_non_editable
        base_notification.COURSE_NOTIFICATION_TYPES[self.default_type_name]['non_editable'] = []
        self._set_notification_config_version(current_config_version + 2)
        new_config = CourseNotificationPreference.get_updated_user_course_preferences(self.user, self.course.id)
        preferences = new_config.notification_preference_config
        preference_non_editable = preferences[self.default_app_name]['non_editable'].get(self.default_type_name, [])
        assert preference_non_editable == []

    def test_non_editable_addition_and_removal_for_core_notification(self):
        """
        Tests if non_editable updates on existing preferences of core notification
        """
        current_config_version = get_course_notification_preference_config_version()
        base_notification.COURSE_NOTIFICATION_APPS[self.default_app_name]['non_editable'] = ['web']
        self._set_notification_config_version(current_config_version + 1)
        new_config = CourseNotificationPreference.get_updated_user_course_preferences(self.user, self.course.id)
        preferences = new_config.notification_preference_config
        preference_non_editable = preferences[self.default_app_name]['non_editable']['core']
        assert 'web' in preference_non_editable
        base_notification.COURSE_NOTIFICATION_APPS[self.default_app_name]['non_editable'] = []
        self._set_notification_config_version(current_config_version + 2)
        new_config = CourseNotificationPreference.get_updated_user_course_preferences(self.user, self.course.id)
        preferences = new_config.notification_preference_config
        preference_non_editable = preferences[self.default_app_name]['non_editable'].get('core', [])
        assert preference_non_editable == []

    def test_notification_type_in_core(self):
        """
        Tests addition/removal of core in notification type
        """
        current_config_version = get_course_notification_preference_config_version()
        base_notification.COURSE_NOTIFICATION_TYPES[self.default_type_name]['is_core'] = True
        self._set_notification_config_version(current_config_version + 1)
        new_config = CourseNotificationPreference.get_updated_user_course_preferences(self.user, self.course.id)
        preferences = new_config.notification_preference_config
        core_notifications = preferences[self.default_app_name]['core_notification_types']
        assert self.default_type_name in core_notifications
        base_notification.COURSE_NOTIFICATION_TYPES[self.default_type_name]['is_core'] = False
        self._set_notification_config_version(current_config_version + 2)
        new_config = CourseNotificationPreference.get_updated_user_course_preferences(self.user, self.course.id)
        preferences = new_config.notification_preference_config
        core_notifications = preferences[self.default_app_name]['core_notification_types']
        assert self.default_type_name not in core_notifications


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
        assert "" not in notification_apps.keys()
        for app_data in notification_apps.values():
            assert 'core_info' in app_data.keys()
            assert isinstance(app_data['non_editable'], list)
            for key in bool_keys:
                assert isinstance(app_data[key], bool)

    def test_validate_core_notification_types(self):
        """
        Tests if COURSE_NOTIFICATION_TYPES constant has all required keys with valid
        data type for core notification type
        """
        str_keys = ['notification_app', 'name', 'email_template']
        notification_types = base_notification.COURSE_NOTIFICATION_TYPES
        assert "" not in notification_types.keys()
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
        assert "" not in notification_types.keys()
        for notification_type in notification_types.values():
            if notification_type['is_core']:
                continue
            assert 'content_template' in notification_type.keys()
            assert isinstance(notification_type['content_context'], dict)
            assert isinstance(notification_type['non_editable'], list)
            for key in str_keys:
                assert isinstance(notification_type[key], str)
            for key in bool_keys:
                assert isinstance(notification_type[key], bool)
