"""
Tests for the python api for course apps.
"""
from unittest import mock
from unittest.mock import Mock

import ddt
from django.test import TestCase
from opaque_keys.edx.locator import CourseLocator

from .utils import make_test_course_app
from ..api import is_course_app_enabled, set_course_app_enabled


@ddt.ddt
@mock.patch("openedx.core.djangoapps.course_apps.api.CourseAppsPluginManager.get_plugin")
class CourseAppsPythonAPITest(TestCase):
    """
    Tests for the python api for course apps.
    """

    def setUp(self) -> None:
        super().setUp()
        self.course_key = CourseLocator(org="org", course="course", run="run")
        self.default_app_id = "test-app"

    @ddt.data(True, False)
    def test_plugin_enabled(self, enabled, get_plugin):
        """
        Test that the is_enabled value is used.
        """
        CourseApp = make_test_course_app(is_available=True)
        get_plugin.return_value = CourseApp
        # Set contradictory value in existing CourseAppStatus to ensure that the `is_enabled` value is
        # being used.
        mock_is_enabled = Mock(return_value=enabled)
        with mock.patch.object(CourseApp, "is_enabled", mock_is_enabled, create=True):
            assert is_course_app_enabled(self.course_key, "test-app") == enabled
            mock_is_enabled.assert_called()

    @ddt.data(True, False)
    def test_set_plugin_enabled(self, enabled, get_plugin):
        """
        Test the behaviour of set_course_app_enabled.
        """
        CourseApp = make_test_course_app(is_available=True)
        get_plugin.return_value = CourseApp
        mock_set_enabled = Mock(return_value=enabled)
        with mock.patch.object(CourseApp, "set_enabled", mock_set_enabled, create=True):
            assert set_course_app_enabled(self.course_key, "test-app", enabled, Mock()) == enabled
            mock_set_enabled.assert_called()
