"""
Tests for SettingsService
"""
import unittest
from unittest import mock
from datetime import datetime, timedelta

import pytest
from django.test import TestCase
import ddt
from pytz import UTC

from config_models.models import ConfigurationModel
from django.conf import settings
from django.test.utils import override_settings
from xblock.runtime import Mixologist

from opaque_keys.edx.locator import CourseLocator
from xmodule.graders import ShowCorrectness
from xmodule.services import ConfigurationService, SettingsService, TeamsConfigurationService, ProblemFeedbackService
from openedx.core.lib.teams_config import TeamsConfig


class _DummyBlock:
    """ Dummy Xblock class """
    pass  # lint-amnesty, pylint: disable=unnecessary-pass


class DummyConfig(ConfigurationModel):
    """
    Dummy Configuration
    """
    class Meta:
        app_label = 'xmoduletestservices'


class DummyUnexpected:
    """
    Dummy Unexpected Class
    """
    pass  # lint-amnesty, pylint: disable=unnecessary-pass


@ddt.ddt
class TestSettingsService(unittest.TestCase):
    """ Test SettingsService """

    xblock_setting_key1 = 'dummy_block'
    xblock_setting_key2 = 'other_dummy_block'

    def setUp(self):
        """ Setting up tests """
        super().setUp()
        self.settings_service = SettingsService()
        self.xblock_mock = mock.Mock()
        self.xblock_mock.block_settings_key = self.xblock_setting_key1
        self.xblock_mock.unmixed_class = mock.Mock()
        self.xblock_mock.unmixed_class.__name__ = self.xblock_setting_key2

    def test_get_given_none_throws_value_error(self):
        """  Test that given None throws value error """
        with pytest.raises(ValueError):
            self.settings_service.get_settings_bucket(None)

    @override_settings()
    def test_get_return_default_if_xblock_settings_is_missing(self):
        """ Test that returns default (or None if default not set) if XBLOCK_SETTINGS is not set """
        # Per django docs, using override_settings() plus 'del' is how to test the absence of a setting:
        del settings.XBLOCK_SETTINGS
        # precondition check
        assert self.settings_service.get_settings_bucket(self.xblock_mock, 'zzz') == 'zzz'

    @override_settings()
    def test_get_return_empty_dictionary_if_xblock_settings_and_default_is_missing(self):
        """ Test that returns default (or None if default not set) if XBLOCK_SETTINGS is not set """
        # Per django docs, using override_settings() plus 'del' is how to test the absence of a setting:
        del settings.XBLOCK_SETTINGS
        # precondition check
        assert self.settings_service.get_settings_bucket(self.xblock_mock) == {}

    @override_settings(XBLOCK_SETTINGS={xblock_setting_key2: {'b': 1}})
    def test_get_returns_none_or_default_if_bucket_not_found(self):
        """ Test if settings service returns default if setting not found """
        assert settings.XBLOCK_SETTINGS == {self.xblock_setting_key2: {'b': 1}}
        assert self.settings_service.get_settings_bucket(self.xblock_mock) == {}
        assert self.settings_service.get_settings_bucket(self.xblock_mock, 123) == 123

    @override_settings(XBLOCK_SETTINGS={xblock_setting_key1: 42})
    def test_get_returns_correct_value(self):
        """ Test if settings service returns correct bucket """
        assert settings.XBLOCK_SETTINGS == {self.xblock_setting_key1: 42}
        assert self.settings_service.get_settings_bucket(self.xblock_mock) == 42

    @override_settings(XBLOCK_SETTINGS={xblock_setting_key2: "I'm a setting"})
    def test_get_respects_block_settings_key(self):
        """ Test if settings service respects block_settings_key value """
        assert settings.XBLOCK_SETTINGS == {self.xblock_setting_key2: "I'm a setting"}
        self.xblock_mock.block_settings_key = self.xblock_setting_key2
        assert self.settings_service.get_settings_bucket(self.xblock_mock) == "I'm a setting"

    @override_settings(XBLOCK_SETTINGS={_DummyBlock.__name__: [1, 2, 3]})
    def test_get_uses_class_name_if_block_settings_key_is_not_set(self):
        """ Test if settings service uses class name if block_settings_key attribute does not exist """
        mixologist = Mixologist([])
        block = mixologist.mix(_DummyBlock)
        assert settings.XBLOCK_SETTINGS == {'_DummyBlock': [1, 2, 3]}
        assert self.settings_service.get_settings_bucket(block) == [1, 2, 3]


class TestConfigurationService(unittest.TestCase):
    """
    Tests for ConfigurationService
    """

    def test_given_unexpected_class_throws_value_error(self):
        """
        Test that instantiating ConfigurationService raises exception on passing
        a class which is not subclass of ConfigurationModel.
        """
        with pytest.raises(ValueError):
            ConfigurationService(DummyUnexpected)

    def test_configuration_service(self):
        """
        Test the correct configuration on instantiating ConfigurationService.
        """
        config_service = ConfigurationService(DummyConfig)
        assert config_service.configuration == DummyConfig


class MockConfigurationService(TeamsConfigurationService):
    """
    Mock ConfigurationService for testing.
    """
    def __init__(self, course, **kwargs):  # lint-amnesty, pylint: disable=unused-argument
        super().__init__()
        self._course = course

    def get_course(self, course_id):
        return self._course


class ConfigurationServiceBaseClass(TestCase):
    """
    Base test class for testing the ConfigurationService.
    """

    def setUp(self):
        super().setUp()

        self.teams_config = TeamsConfig(
            {'max_size': 2, 'topics': [{'id': 'topic', 'name': 'Topic', 'description': 'A Topic'}]}
        )
        self.course = mock.Mock(
            id=CourseLocator('org_0', 'course_0', 'run_0'),
            teams_configuration=self.teams_config
        )
        self.configuration_service = MockConfigurationService(self.course)


class TestTeamsConfigurationService(ConfigurationServiceBaseClass):
    """
    Test operations of the teams configuration service
    """

    def test_get_teamsconfiguration(self):
        teams_config = self.configuration_service.get_teams_configuration(self.course.id)
        assert teams_config == self.teams_config


@ddt.ddt
class TestProblemFeedbackService(unittest.TestCase):
    """
    Tests the correctness_available method
    """

    def setUp(self):
        super().setUp()
        self._xblock = mock.MagicMock()
        now = datetime.now(UTC)
        day_delta = timedelta(days=1)
        self.yesterday = now - day_delta
        self.today = now
        self.tomorrow = now + day_delta

    def test_show_correctness_default(self):
        """
        Test that correctness is visible by default.
        """
        assert ProblemFeedbackService(self._xblock).correctness_available()

    @ddt.data(
        (ShowCorrectness.ALWAYS, True),
        (ShowCorrectness.ALWAYS, False),
        # Any non-constant values behave like "always"
        ('', True),
        ('', False),
        ('other-value', True),
        ('other-value', False),
    )
    @ddt.unpack
    def test_show_correctness_always(self, show_correctness, has_staff_access):
        """
        Test that correctness is visible when show_correctness is turned on.
        """
        self._xblock.show_correctness = show_correctness
        assert ProblemFeedbackService(self._xblock, user_is_staff=has_staff_access).correctness_available()

    @ddt.data(True, False)
    def test_show_correctness_never(self, has_staff_access):
        """
        Test that show_correctness="never" hides correctness from learners and course staff.
        """
        self._xblock.show_correctness = ShowCorrectness.NEVER
        assert not ProblemFeedbackService(self._xblock, user_is_staff=has_staff_access).correctness_available()

    @ddt.data(
        # Correctness not visible to learners if due date in the future
        ('tomorrow', False, False),
        # Correctness is visible to learners if due date in the past
        ('yesterday', False, True),
        # Correctness is visible to learners if due date in the past (just)
        ('today', False, True),
        # Correctness is visible to learners if there is no due date
        (None, False, True),
        # Correctness is visible to staff if due date in the future
        ('tomorrow', True, True),
        # Correctness is visible to staff if due date in the past
        ('yesterday', True, True),
        # Correctness is visible to staff if there is no due date
        (None, True, True),
    )
    @ddt.unpack
    def test_show_correctness_past_due(self, due_date_str, has_staff_access, expected_result):
        """
        Test show_correctness="past_due" to ensure:
        * correctness is always visible to course staff
        * correctness is always visible to everyone if there is no due date
        * correctness is visible to learners after the due date, when there is a due date.
        """
        self._xblock.show_correctness = ShowCorrectness.PAST_DUE
        if due_date_str is None:
            self._xblock.due = None
            self._xblock.close_date = None
        else:
            self._xblock.due = getattr(self, due_date_str)
            self._xblock.close_date = getattr(self, due_date_str)
        assert ProblemFeedbackService(self._xblock, user_is_staff=has_staff_access).correctness_available() ==\
               expected_result
