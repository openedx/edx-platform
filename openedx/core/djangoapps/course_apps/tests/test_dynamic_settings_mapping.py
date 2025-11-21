"""
Tests for dynamic course app settings mapping functionality.
"""
from unittest.mock import patch

from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from openedx.core.djangoapps.course_apps.plugins import CourseAppsPluginManager, CourseApp


class MockCourseAppWithSetting(CourseApp):
    """Mock course app with an advanced setting field."""

    app_id = "settings_app"
    name = "Settings App"
    description = "An app with advanced settings"
    advanced_setting_field = "settings_app_field"

    @classmethod
    def is_available(cls, course_key):
        return True

    @classmethod
    def is_enabled(cls, course_key):
        return True

    @classmethod
    def set_enabled(cls, course_key, enabled, user):
        return enabled

    @classmethod
    def get_allowed_operations(cls, course_key, user=None):
        return {"enable": True, "configure": True}


class MockCourseAppNoSettings(CourseApp):
    """Mock course app with no advanced settings mapping."""

    app_id = "no_settings_app"
    name = "No Settings App"
    description = "An app without advanced settings"

    @classmethod
    def is_available(cls, course_key):
        return True

    @classmethod
    def is_enabled(cls, course_key):
        return True

    @classmethod
    def set_enabled(cls, course_key, enabled, user):
        return enabled

    @classmethod
    def get_allowed_operations(cls, course_key, user=None):
        return {"enable": True, "configure": True}


class DynamicSettingsMappingTest(SharedModuleStoreTestCase):
    """Test dynamic course app settings mapping functionality."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.course = CourseFactory.create()

    def test_app_with_advanced_setting_mapping(self):
        """Test that a course app with an advanced setting field is mapped correctly."""
        mock_plugins = {
            "settings_app": MockCourseAppWithSetting(),
        }

        with patch('edx_django_utils.plugins.PluginManager.get_available_plugins', return_value=mock_plugins):
            mapping = CourseAppsPluginManager.get_course_app_settings_mapping(self.course.id)

            self.assertIn("settings_app_field", mapping)
            self.assertEqual(mapping["settings_app_field"], "settings_app")

    def test_no_advanced_setting_fields(self):
        """Test that a course app without advanced_setting_fields is not included in mapping."""
        mock_plugins = {
            "no_settings_app": MockCourseAppNoSettings(),
        }

        with patch('edx_django_utils.plugins.PluginManager.get_available_plugins', return_value=mock_plugins):
            mapping = CourseAppsPluginManager.get_course_app_settings_mapping(self.course.id)

            self.assertEqual(len(mapping), 0)

    def test_mixed_apps_mapping(self):
        """Test mapping with a mix of apps with and without advanced settings."""
        mock_plugins = {
            "settings_app": MockCourseAppWithSetting(),
            "no_settings_app": MockCourseAppNoSettings(),
        }

        with patch('edx_django_utils.plugins.PluginManager.get_available_plugins', return_value=mock_plugins):
            mapping = CourseAppsPluginManager.get_course_app_settings_mapping(self.course.id)

            # Should only include apps with advanced_setting_field
            self.assertEqual(len(mapping), 1)
            self.assertEqual(mapping["settings_app_field"], "settings_app")
