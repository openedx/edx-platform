"""
Test utilities for course apps.
"""
from typing import Type

from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.course_apps.plugins import CourseApp


def make_test_course_app(
    app_id: str = "test-app",
    name: str = "Test Course App",
    description: str = "Test Course App Description",
    is_available: bool = True,
) -> Type[CourseApp]:
    """
    Creates a test plugin entrypoint based on provided parameters."""

    class TestCourseApp(CourseApp):
        """
        Course App Config for use in tests.
        """

        app_id = ""
        name = ""
        description = ""
        _enabled = {}

        @classmethod
        def is_available(cls, course_key):  # pylint=disable=unused-argument
            """
            Return value provided to function"""
            return is_available

        @classmethod
        def get_allowed_operations(cls, course_key, user=None):  # pylint=disable=unused-argument
            """
            Return dummy values for allowed operations."""
            return {
                "enable": True,
                "configure": True,
            }

        @classmethod
        def set_enabled(cls, course_key: CourseKey, enabled: bool, user: 'User') -> bool:
            cls._enabled[course_key] = enabled
            return enabled

        @classmethod
        def is_enabled(cls, course_key: CourseKey) -> bool:
            return cls._enabled.get(course_key, False)

    TestCourseApp.app_id = app_id
    TestCourseApp.name = name
    TestCourseApp.description = description
    return TestCourseApp
