"""Course app config for courseware apps."""
from typing import Dict, Optional

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_noop as _
from opaque_keys.edx.keys import CourseKey
from xmodule.modulestore.django import modulestore

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.course_apps.plugins import CourseApp
from openedx.core.lib.courses import get_course_by_id

User = get_user_model()

TEXTBOOK_ENABLED = settings.FEATURES.get("ENABLE_TEXTBOOK", False)


class ProgressCourseApp(CourseApp):
    """
    Course app config for progress app.
    """

    app_id = "progress"
    name = _("Progress")
    description = _("Allow students to track their progress throughout the course.")

    @classmethod
    def is_available(cls, course_key: CourseKey) -> bool:
        """
        The progress course app is always available.
        """
        return True

    @classmethod
    def is_enabled(cls, course_key: CourseKey) -> bool:
        """
        The progress course status is stored in the course module.
        """
        return not CourseOverview.get_from_id(course_key).hide_progress_tab

    @classmethod
    def set_enabled(cls, course_key: CourseKey, enabled: bool, user: 'User') -> bool:
        """
        The progress course enabled/disabled status is stored in the course module.
        """
        course = get_course_by_id(course_key)
        course.hide_progress_tab = not enabled
        modulestore().update_item(course, user.id)
        return enabled

    @classmethod
    def get_allowed_operations(cls, course_key: CourseKey, user: Optional[User] = None) -> Dict[str, bool]:
        """
        Returns the allowed operations for the app.
        """
        return {
            "enable": True,
            "configure": True,
        }


class TextbooksCourseApp(CourseApp):
    """
    Course app config for textbooks app.
    """

    app_id = "textbooks"
    name = _("Textbooks")
    description = _("Provide links to applicable resources for your course.")

    @classmethod
    def is_available(cls, course_key: CourseKey) -> bool:  # pylint: disable=unused-argument
        """
        The textbook app can be made available globally using a value in features.
        """
        return TEXTBOOK_ENABLED

    @classmethod
    def is_enabled(cls, course_key: CourseKey) -> bool:  # pylint: disable=unused-argument
        """
        Returns if the textbook app is globally enabled.
        """
        return TEXTBOOK_ENABLED

    @classmethod
    def set_enabled(cls, course_key: CourseKey, enabled: bool, user: 'User') -> bool:
        """
        The textbook app can be globally enabled/disabled.

        Currently, it isn't possible to enable/disable this app on a per-course basis.
        """
        raise ValueError("The textbook app can not be enabled/disabled for a single course.")

    @classmethod
    def get_allowed_operations(cls, course_key: CourseKey, user: Optional[User] = None) -> Dict[str, bool]:
        """
        Returns the allowed operations for the app.
        """
        return {
            # Either the app is available and configurable or not. You cannot disable it from the API yet.
            "enable": False,
            "configure": True,
        }


class CalculatorCourseApp(CourseApp):
    """
    Course App config for calculator app.
    """

    app_id = "calculator"
    name = _("Calculator")
    description = _("Provide an in-browser calculator that supports simple and complex calculations.")

    @classmethod
    def is_available(cls, course_key: CourseKey) -> bool:
        """
        Calculator is available for all courses.
        """
        return True

    @classmethod
    def is_enabled(cls, course_key: CourseKey) -> bool:
        """
        Get calculator enabled status from course overview model.
        """
        return CourseOverview.get_from_id(course_key).show_calculator

    @classmethod
    def set_enabled(cls, course_key: CourseKey, enabled: bool, user: 'User') -> bool:
        """
        Update calculator enabled status in modulestore.
        """
        course = get_course_by_id(course_key)
        course.show_calculator = enabled
        modulestore().update_item(course, user.id)
        return enabled

    @classmethod
    def get_allowed_operations(cls, course_key: CourseKey, user: Optional[User] = None) -> Dict[str, bool]:
        """
        Get allowed operations for calculator app.
        """
        return {
            "enable": True,
            # There is nothing to configure for calculator yet.
            "configure": False,
        }
