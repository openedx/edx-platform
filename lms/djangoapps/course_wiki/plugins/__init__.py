"""Module with the course app configuration for the Wiki."""
from typing import Dict, Optional, TYPE_CHECKING

from django.conf import settings
from django.utils.translation import gettext_noop as _
from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.course_apps.plugins import CourseApp

# Import the User model only for type checking since importing it at runtime
# will prevent the app from starting since the model is imported before
# Django's machinery is ready.
if TYPE_CHECKING:
    from django.contrib.auth import get_user_model
    User = get_user_model()

WIKI_ENABLED = settings.WIKI_ENABLED


class WikiCourseApp(CourseApp):
    """
    Course app for the Wiki.
    """

    app_id = "wiki"
    name = _("Wiki")
    description = _("Enable learners to access, and collaborate on course-related information.")
    documentation_links = {
        "learn_more_configuration": settings.WIKI_HELP_URL,
    }

    @classmethod
    def is_available(cls, course_key: CourseKey) -> bool:  # pylint: disable=unused-argument
        """
        Returns if the app is available for the course.

        The wiki is available for all courses or none of them depending on the a Django setting.
        """
        return WIKI_ENABLED

    @classmethod
    def is_enabled(cls, course_key: CourseKey) -> bool:  # pylint: disable=unused-argument
        """
        Returns if the wiki is available for the course.

        The wiki currently cannot be enabled or disabled on a per-course basis.
        """
        return WIKI_ENABLED

    @classmethod
    def set_enabled(cls, course_key: CourseKey, enabled: bool, user: 'User') -> bool:
        """
        The wiki cannot be enabled or disabled.
        """
        # Currently, you cannot enable/disable wiki via the API
        raise ValueError("Wiki cannot be enabled/disabled vis this API.")

    @classmethod
    def get_allowed_operations(cls, course_key: CourseKey, user: Optional['User'] = None) -> Dict[str, bool]:
        """
        Returns the operations you can perform on the wiki.
        """
        return {
            # The wiki cannot be enabled/disabled via the API yet.
            "enable": False,
            # There is nothing to configure for Wiki yet.
            "configure": False,
        }
