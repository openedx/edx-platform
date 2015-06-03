"""
Definition of the course team feature.
"""

from django.utils.translation import ugettext as _
from courseware.tabs import EnrolledCourseViewType
from .views import is_feature_enabled


class TeamsCourseViewType(EnrolledCourseViewType):
    """
    The representation of the course teams view type.
    """

    name = "teams"
    title = _("Teams")
    view_name = "teams_dashboard"

    @classmethod
    def is_enabled(cls, course, user=None):
        """Returns true if the teams feature is enabled in the course.

        Args:
            course (CourseDescriptor): the course using the feature
            user (User): the user interacting with the course
        """
        if not super(TeamsCourseViewType, cls).is_enabled(course, user=user):
            return False

        return is_feature_enabled(course)
