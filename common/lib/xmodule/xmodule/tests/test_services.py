"""
Tests for SettingsService
"""

import ddt
import mock
from unittest import TestCase

from django.conf import settings
from django.test.utils import override_settings

from xblock.runtime import Mixologist
from xmodule.services import SettingsService, NotificationsService


class _DummyBlock(object):
    """ Dummy Xblock class """
    pass


@ddt.ddt
class TestSettingsService(TestCase):
    """ Test SettingsService """

    xblock_setting_key1 = 'dummy_block'
    xblock_setting_key2 = 'other_dummy_block'

    def setUp(self):
        """ Setting up tests """
        super(TestSettingsService, self).setUp()
        self.settings_service = SettingsService()
        self.xblock_mock = mock.Mock()
        self.xblock_mock.block_settings_key = self.xblock_setting_key1
        self.xblock_mock.unmixed_class = mock.Mock()
        self.xblock_mock.unmixed_class.__name__ = self.xblock_setting_key2

    def test_get_given_none_throws_value_error(self):
        """  Test that given None throws value error """
        with self.assertRaises(ValueError):
            self.settings_service.get_settings_bucket(None)

    def test_get_return_default_if_xblock_settings_is_missing(self):
        """ Test that returns default (or None if default not set) if XBLOCK_SETTINGS is not set """
        self.assertFalse(hasattr(settings, 'XBLOCK_SETTINGS'))  # precondition check
        self.assertEqual(self.settings_service.get_settings_bucket(self.xblock_mock, 'zzz'), 'zzz')

    def test_get_return_empty_dictionary_if_xblock_settings_and_default_is_missing(self):
        """ Test that returns default (or None if default not set) if XBLOCK_SETTINGS is not set """
        self.assertFalse(hasattr(settings, 'XBLOCK_SETTINGS'))  # precondition check
        self.assertEqual(self.settings_service.get_settings_bucket(self.xblock_mock), {})

    @override_settings(XBLOCK_SETTINGS={xblock_setting_key2: {'b': 1}})
    def test_get_returns_none_or_default_if_bucket_not_found(self):
        """ Test if settings service returns default if setting not found """
        self.assertEqual(settings.XBLOCK_SETTINGS, {self.xblock_setting_key2: {'b': 1}})
        self.assertEqual(self.settings_service.get_settings_bucket(self.xblock_mock), {})
        self.assertEqual(self.settings_service.get_settings_bucket(self.xblock_mock, 123), 123)

    @override_settings(XBLOCK_SETTINGS={xblock_setting_key1: 42})
    def test_get_returns_correct_value(self):
        """ Test if settings service returns correct bucket """
        self.assertEqual(settings.XBLOCK_SETTINGS, {self.xblock_setting_key1: 42})
        self.assertEqual(self.settings_service.get_settings_bucket(self.xblock_mock), 42)

    @override_settings(XBLOCK_SETTINGS={xblock_setting_key2: "I'm a setting"})
    def test_get_respects_block_settings_key(self):
        """ Test if settings service respects block_settings_key value """
        self.assertEqual(settings.XBLOCK_SETTINGS, {self.xblock_setting_key2: "I'm a setting"})
        self.xblock_mock.block_settings_key = self.xblock_setting_key2
        self.assertEqual(self.settings_service.get_settings_bucket(self.xblock_mock), "I'm a setting")

    @override_settings(XBLOCK_SETTINGS={_DummyBlock.__name__: [1, 2, 3]})
    def test_get_uses_class_name_if_block_settings_key_is_not_set(self):
        """ Test if settings service uses class name if block_settings_key attribute does not exist """
        mixologist = Mixologist([])
        block = mixologist.mix(_DummyBlock)
        self.assertEqual(settings.XBLOCK_SETTINGS, {"_DummyBlock": [1, 2, 3]})
        self.assertEqual(self.settings_service.get_settings_bucket(block), [1, 2, 3])


class TestNotificationsService(TestCase):
    """ Test SettingsService """

    def setUp(self):
        """ Setting up tests """
        super(TestNotificationsService, self).setUp()
        self.notifications_service = NotificationsService()

    def test_exposed_functions(self):
        """
        Make sure the service exposes all of the edx_notifications library functions (that we know about for now)
        """

        # publisher lib
        self.assertTrue(hasattr(self.notifications_service, 'register_notification_type'))
        self.assertTrue(hasattr(self.notifications_service, 'get_notification_type'))
        self.assertTrue(hasattr(self.notifications_service, 'get_all_notification_types'))
        self.assertTrue(hasattr(self.notifications_service, 'publish_notification_to_user'))
        self.assertTrue(hasattr(self.notifications_service, 'bulk_publish_notification_to_users'))

        # consumer lib
        self.assertTrue(hasattr(self.notifications_service, 'get_notifications_count_for_user'))
        self.assertTrue(hasattr(self.notifications_service, 'get_notification_for_user'))
        self.assertTrue(hasattr(self.notifications_service, 'get_notifications_for_user'))
        self.assertTrue(hasattr(self.notifications_service, 'mark_notification_read'))
        self.assertTrue(hasattr(self.notifications_service, 'mark_all_user_notification_as_read'))
