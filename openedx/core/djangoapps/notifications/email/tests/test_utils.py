"""
Test utils.py
"""
import datetime
import ddt
import pytest

from django.http.response import Http404
from itertools import product
from pytz import utc
from waffle import get_waffle_flag_model   # pylint: disable=invalid-django-waffle-import

from common.djangoapps.student.tests.factories import UserFactory
from openedx.core.djangoapps.notifications.base_notification import (
    COURSE_NOTIFICATION_APPS,
    COURSE_NOTIFICATION_TYPES,
)
from openedx.core.djangoapps.notifications.config.waffle import ENABLE_EMAIL_NOTIFICATIONS
from openedx.core.djangoapps.notifications.email_notifications import EmailCadence
from openedx.core.djangoapps.notifications.models import CourseNotificationPreference, Notification
from openedx.core.djangoapps.notifications.email.utils import (
    add_additional_attributes_to_notifications,
    create_app_notifications_dict,
    create_datetime_string,
    create_email_digest_context,
    create_email_template_context,
    decrypt_object,
    decrypt_string,
    encrypt_object,
    encrypt_string,
    get_course_info,
    get_time_ago,
    is_email_notification_flag_enabled,
    update_user_preferences_from_patch,
)
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from .utils import assert_list_equal, create_notification


class TestUtilFunctions(ModuleStoreTestCase):
    """
    Test utils functions
    """
    def setUp(self):
        """
        Setup
        """
        super().setUp()
        self.user = UserFactory()
        self.course = CourseFactory.create(display_name='test course', run="Testing_course")

    def test_additional_attributes(self):
        """
        Tests additional attributes are added when notifications list is passed to
        add_additional_attributes_to_notifications function
        """
        notification = create_notification(self.user, self.course.id)
        additional_params = ['course_name', 'icon', 'time_ago']
        for param in additional_params:
            assert not hasattr(notification, param)
        add_additional_attributes_to_notifications([notification])
        for param in additional_params:
            assert hasattr(notification, param)

    def test_create_app_notifications_dict(self):
        """
        Tests notifications are divided based on their app_name
        """
        Notification.objects.all().delete()
        create_notification(self.user, self.course.id, app_name='discussion', notification_type='new_comment')
        create_notification(self.user, self.course.id, app_name='updates', notification_type='course_update')
        app_dict = create_app_notifications_dict(Notification.objects.all())
        assert len(app_dict.keys()) == 2
        for key in ['discussion', 'updates']:
            assert key in app_dict.keys()
            assert app_dict[key]['count'] == 1
            assert len(app_dict[key]['notifications']) == 1

    def test_get_course_info(self):
        """
        Tests get_course_info function
        """
        assert get_course_info(self.course.id) == {'name': 'test course'}

    def test_get_time_ago(self):
        """
        Tests time_ago string
        """
        current_datetime = utc.localize(datetime.datetime.now())
        assert "Today" == get_time_ago(current_datetime)
        assert "1d" == get_time_ago(current_datetime - datetime.timedelta(days=1))
        assert "1w" == get_time_ago(current_datetime - datetime.timedelta(days=7))

    def test_datetime_string(self):
        dt = datetime.datetime(2024, 3, 25)
        assert create_datetime_string(dt) == "Monday, Mar 25"


@ddt.ddt
class TestContextFunctions(ModuleStoreTestCase):
    """
    Test template context functions in utils.py
    """
    def setUp(self):
        """
        Setup
        """
        super().setUp()
        self.user = UserFactory()
        self.course = CourseFactory.create(display_name='test course', run="Testing_course")

    def test_email_template_context(self):
        """
        Tests common header and footer context
        """
        context = create_email_template_context(self.user.username)
        keys = ['platform_name', 'mailing_address', 'logo_url', 'social_media',
                'notification_settings_url', 'unsubscribe_url']
        for key in keys:
            assert key in context

    @ddt.data('Daily', 'Weekly')
    def test_email_digest_context(self, digest_frequency):
        """
        Tests context for email digest
        """
        Notification.objects.all().delete()
        discussion_notification = create_notification(self.user, self.course.id, app_name='discussion',
                                                      notification_type='new_comment')
        update_notification = create_notification(self.user, self.course.id, app_name='updates',
                                                  notification_type='course_update')
        app_dict = create_app_notifications_dict(Notification.objects.all())
        end_date = datetime.datetime(2024, 3, 24, 12, 0)
        params = {
            "app_notifications_dict": app_dict,
            "username": self.user.username,
            "start_date": end_date - datetime.timedelta(days=0 if digest_frequency == "Daily" else 6),
            "end_date": end_date,
            "digest_frequency": digest_frequency,
            "courses_data": None
        }
        context = create_email_digest_context(**params)
        expected_start_date = 'Sunday, Mar 24' if digest_frequency == 'Daily' else 'Monday, Mar 18'
        expected_digest_updates = [
            {'title': 'Total Notifications', 'count': 2},
            {'title': 'Discussion', 'count': 1},
            {'title': 'Updates', 'count': 1},
        ]
        expected_email_content = [
            {'title': 'Discussion', 'help_text': '', 'help_text_url': '', 'notifications': [discussion_notification]},
            {'title': 'Updates', 'help_text': '', 'help_text_url': '', 'notifications': [update_notification]}
        ]
        assert context['start_date'] == expected_start_date
        assert context['end_date'] == 'Sunday, Mar 24'
        assert context['digest_frequency'] == digest_frequency
        assert_list_equal(context['email_digest_updates'], expected_digest_updates)
        assert_list_equal(context['email_content'], expected_email_content)


class TestWaffleFlag(ModuleStoreTestCase):
    """
    Test user level email notifications waffle flag
    """
    def setUp(self):
        """
        Setup
        """
        super().setUp()
        self.user_1 = UserFactory()
        self.user_2 = UserFactory()
        self.course_1 = CourseFactory.create(display_name='test course 1', run="Testing_course_1")
        self.course_1 = CourseFactory.create(display_name='test course 2', run="Testing_course_2")

    def test_waffle_flag_for_everyone(self):
        """
        Tests if waffle flag is enabled for everyone
        """
        assert is_email_notification_flag_enabled() is False
        waffle_model = get_waffle_flag_model()
        flag, _ = waffle_model.objects.get_or_create(name=ENABLE_EMAIL_NOTIFICATIONS.name)
        flag.everyone = True
        flag.save()
        assert is_email_notification_flag_enabled() is True

    def test_waffle_flag_for_user(self):
        """
        Tests user level waffle flag
        """
        assert is_email_notification_flag_enabled() is False
        waffle_model = get_waffle_flag_model()
        flag, _ = waffle_model.objects.get_or_create(name=ENABLE_EMAIL_NOTIFICATIONS.name)
        flag.users.add(self.user_1)
        flag.save()
        assert is_email_notification_flag_enabled(self.user_1) is True
        assert is_email_notification_flag_enabled(self.user_2) is False

    def test_waffle_flag_everyone_priority(self):
        """
        Tests if everyone field has more priority over user field
        """
        assert is_email_notification_flag_enabled() is False
        waffle_model = get_waffle_flag_model()
        flag, _ = waffle_model.objects.get_or_create(name=ENABLE_EMAIL_NOTIFICATIONS.name)
        flag.everyone = False
        flag.users.add(self.user_1)
        flag.save()
        assert is_email_notification_flag_enabled() is False
        assert is_email_notification_flag_enabled(self.user_1) is False
        assert is_email_notification_flag_enabled(self.user_2) is False


class TestEncryption(ModuleStoreTestCase):
    """
    Tests all encryption methods
    """
    def test_string_encryption(self):
        """
        Tests if decrypted string is equal original string
        """
        string = "edx"
        encrypted = encrypt_string(string)
        decrypted = decrypt_string(encrypted)
        assert string == decrypted

    def test_object_encryption(self):
        """
        Tests if decrypted object is equal to original object
        """
        obj = {
            'org': 'edx'
        }
        encrypted = encrypt_object(obj)
        decrypted = decrypt_object(encrypted)
        assert obj == decrypted


@ddt.ddt
class TestUpdatePreferenceFromPatch(ModuleStoreTestCase):
    """
    Tests if preferences are update according to patch data
    """
    def setUp(self):
        """
        Setup test cases
        """
        super().setUp()
        self.user = UserFactory()
        self.course_1 = CourseFactory.create(display_name='test course 1', run="Testing_course_1")
        self.course_2 = CourseFactory.create(display_name='test course 2', run="Testing_course_2")
        self.preference_1 = CourseNotificationPreference(course_id=self.course_1.id, user=self.user)
        self.preference_2 = CourseNotificationPreference(course_id=self.course_2.id, user=self.user)
        self.preference_1.save()
        self.preference_2.save()
        self.default_json = self.preference_1.notification_preference_config

    def is_channel_editable(self, app_name, notification_type, channel):
        """
        Returns if channel is editable
        """
        if notification_type == 'core':
            return channel not in COURSE_NOTIFICATION_APPS[app_name]['non_editable']
        return channel not in COURSE_NOTIFICATION_TYPES[notification_type]['non_editable']

    def get_default_cadence_value(self, app_name, notification_type):
        """
        Returns default email cadence value
        """
        if notification_type == 'core':
            return COURSE_NOTIFICATION_APPS[app_name]['core_email_cadence']
        return COURSE_NOTIFICATION_TYPES[notification_type]['email_cadence']

    @ddt.data(True, False)
    def test_value_param(self, new_value):
        """
        Tests if value is updated for all notification types and for all channels
        """
        encrypted_username = encrypt_string(self.user.username)
        encrypted_patch = encrypt_object({
            'value': new_value
        })
        update_user_preferences_from_patch(encrypted_username, encrypted_patch)
        preference_1 = CourseNotificationPreference.objects.get(course_id=self.course_1.id, user=self.user)
        preference_2 = CourseNotificationPreference.objects.get(course_id=self.course_2.id, user=self.user)
        for preference in [preference_1, preference_2]:
            config = preference.notification_preference_config
            for app_name, app_prefs in config.items():
                for noti_type, type_prefs in app_prefs['notification_types'].items():
                    for channel in ['web', 'email', 'push']:
                        if self.is_channel_editable(app_name, noti_type, channel):
                            assert type_prefs[channel] == new_value
                        else:
                            default_app_json = self.default_json[app_name]
                            default_notification_type_json = default_app_json['notification_types'][noti_type]
                            assert type_prefs[channel] == default_notification_type_json[channel]

    @ddt.data(*product(['web', 'email', 'push'], [True, False]))
    @ddt.unpack
    def test_value_with_channel_param(self, param_channel, new_value):
        """
        Tests if value is updated only for channel
        """
        encrypted_username = encrypt_string(self.user.username)
        encrypted_patch = encrypt_object({
            'channel': param_channel,
            'value': new_value
        })
        update_user_preferences_from_patch(encrypted_username, encrypted_patch)
        preference_1 = CourseNotificationPreference.objects.get(course_id=self.course_1.id, user=self.user)
        preference_2 = CourseNotificationPreference.objects.get(course_id=self.course_2.id, user=self.user)
        # pylint: disable=too-many-nested-blocks
        for preference in [preference_1, preference_2]:
            config = preference.notification_preference_config
            for app_name, app_prefs in config.items():
                for noti_type, type_prefs in app_prefs['notification_types'].items():
                    for channel in ['web', 'email', 'push']:
                        if not self.is_channel_editable(app_name, noti_type, channel):
                            continue
                        if channel == param_channel:
                            assert type_prefs[channel] == new_value
                            if channel == 'email':
                                cadence_value = EmailCadence.NEVER
                                if new_value:
                                    cadence_value = self.get_default_cadence_value(app_name, noti_type)
                                assert type_prefs['email_cadence'] == cadence_value
                        else:
                            default_app_json = self.default_json[app_name]
                            default_notification_type_json = default_app_json['notification_types'][noti_type]
                            assert type_prefs[channel] == default_notification_type_json[channel]

    @ddt.data(True, False)
    def test_value_with_course_id_param(self, new_value):
        """
        Tests if value is updated for a single course only
        """
        encrypted_username = encrypt_string(self.user.username)
        encrypted_patch = encrypt_object({
            'value': new_value,
            'course_id': str(self.course_1.id),
        })
        update_user_preferences_from_patch(encrypted_username, encrypted_patch)

        preference_2 = CourseNotificationPreference.objects.get(course_id=self.course_2.id, user=self.user)
        self.assertDictEqual(preference_2.notification_preference_config, self.default_json)

        preference_1 = CourseNotificationPreference.objects.get(course_id=self.course_1.id, user=self.user)
        config = preference_1.notification_preference_config
        for app_name, app_prefs in config.items():
            for noti_type, type_prefs in app_prefs['notification_types'].items():
                for channel in ['web', 'email', 'push']:
                    if self.is_channel_editable(app_name, noti_type, channel):
                        assert type_prefs[channel] == new_value
                    else:
                        default_app_json = self.default_json[app_name]
                        default_notification_type_json = default_app_json['notification_types'][noti_type]
                        assert type_prefs[channel] == default_notification_type_json[channel]

    @ddt.data(*product(['discussion', 'updates'], [True, False]))
    @ddt.unpack
    def test_value_with_app_name_param(self, param_app_name, new_value):
        """
        Tests if value is updated only for channel
        """
        encrypted_username = encrypt_string(self.user.username)
        encrypted_patch = encrypt_object({
            'app_name': param_app_name,
            'value': new_value
        })
        update_user_preferences_from_patch(encrypted_username, encrypted_patch)
        preference_1 = CourseNotificationPreference.objects.get(course_id=self.course_1.id, user=self.user)
        preference_2 = CourseNotificationPreference.objects.get(course_id=self.course_2.id, user=self.user)
        # pylint: disable=too-many-nested-blocks
        for preference in [preference_1, preference_2]:
            config = preference.notification_preference_config
            for app_name, app_prefs in config.items():
                for noti_type, type_prefs in app_prefs['notification_types'].items():
                    for channel in ['web', 'email', 'push']:
                        if not self.is_channel_editable(app_name, noti_type, channel):
                            continue
                        if app_name == param_app_name:
                            assert type_prefs[channel] == new_value
                            if channel == 'email':
                                cadence_value = EmailCadence.NEVER
                                if new_value:
                                    cadence_value = self.get_default_cadence_value(app_name, noti_type)
                                assert type_prefs['email_cadence'] == cadence_value
                        else:
                            default_app_json = self.default_json[app_name]
                            default_notification_type_json = default_app_json['notification_types'][noti_type]
                            assert type_prefs[channel] == default_notification_type_json[channel]

    @ddt.data(*product(['new_discussion_post', 'content_reported'], [True, False]))
    @ddt.unpack
    def test_value_with_notification_type_param(self, param_notification_type, new_value):
        """
        Tests if value is updated only for channel
        """
        encrypted_username = encrypt_string(self.user.username)
        encrypted_patch = encrypt_object({
            'notification_type': param_notification_type,
            'value': new_value
        })
        update_user_preferences_from_patch(encrypted_username, encrypted_patch)
        preference_1 = CourseNotificationPreference.objects.get(course_id=self.course_1.id, user=self.user)
        preference_2 = CourseNotificationPreference.objects.get(course_id=self.course_2.id, user=self.user)
        # pylint: disable=too-many-nested-blocks
        for preference in [preference_1, preference_2]:
            config = preference.notification_preference_config
            for app_name, app_prefs in config.items():
                for noti_type, type_prefs in app_prefs['notification_types'].items():
                    for channel in ['web', 'email', 'push']:
                        if not self.is_channel_editable(app_name, noti_type, channel):
                            continue
                        if noti_type == param_notification_type:
                            assert type_prefs[channel] == new_value
                            if channel == 'email':
                                cadence_value = EmailCadence.NEVER
                                if new_value:
                                    cadence_value = self.get_default_cadence_value(app_name, noti_type)
                                assert type_prefs['email_cadence'] == cadence_value
                        else:
                            default_app_json = self.default_json[app_name]
                            default_notification_type_json = default_app_json['notification_types'][noti_type]
                            assert type_prefs[channel] == default_notification_type_json[channel]

    def test_preference_not_updated_if_invalid_username(self):
        """
        Tests if no preference is updated when username is not valid
        """
        username = f"{self.user.username}-updated"
        enc_username = encrypt_string(username)
        enc_patch = encrypt_object({"value": True})
        with pytest.raises(Http404):
            update_user_preferences_from_patch(enc_username, enc_patch)
