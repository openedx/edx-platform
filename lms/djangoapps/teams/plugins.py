"""
Definition of the course team feature.
"""
from typing import Dict, Optional

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_noop as _
from opaque_keys.edx.keys import CourseKey

from lms.djangoapps.courseware.tabs import EnrolledTab
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.course_apps.plugins import CourseApp
from . import is_feature_enabled


User = get_user_model()


class TeamsTab(EnrolledTab):
    """
    The representation of the course teams view type.
    """

    type = "teams"
    title = _("Teams")
    view_name = "teams_dashboard"

    @classmethod
    def is_enabled(cls, course, user=None):
        """Returns true if the teams feature is enabled in the course.

        Args:
            course (CourseBlock): the course using the feature
            user (User): the user interacting with the course
        """
        if not super().is_enabled(course, user=user):
            return False

        return is_feature_enabled(course)


class TeamsCourseApp(CourseApp):
    """
    Course app for teams.
    """

    app_id = "teams"
    name = _("Teams")
    description = _("Leverage teams to allow learners to connect by topic of interest.")
    documentation_links = {
        "learn_more_configuration": settings.TEAMS_HELP_URL,
    }

    @classmethod
    def is_available(cls, course_key: CourseKey) -> bool:
        """
        The teams app is currently available globally based on a feature setting.
        """
        return settings.FEATURES.get("ENABLE_TEAMS", False)

    @classmethod
    def is_enabled(cls, course_key: CourseKey) -> bool:
        return CourseOverview.get_from_id(course_key).teams_enabled

    @classmethod
    def set_enabled(cls, course_key: CourseKey, enabled: bool, user: User) -> bool:
        raise ValueError("Teams cannot be enabled/disabled via this API.")

    @classmethod
    def get_allowed_operations(cls, course_key: CourseKey, user: Optional[User] = None) -> Dict[str, bool]:
        """
        Return allowed operations for teams app.
        """
        return {
            "enable": False,
            "configure": True,
        }
