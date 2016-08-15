"""
Definition of the course team feature.
"""
from django.utils.translation import ugettext_noop
from courseware.tabs import EnrolledTab
from . import is_feature_enabled


class TeamsTab(EnrolledTab):
    """
    The representation of the course teams view type.
    """

    type = "teams"
    title = ugettext_noop("Teams")
    view_name = "teams_dashboard"

    @classmethod
    def is_enabled(cls, course, user=None):
        """Returns true if the teams feature is enabled in the course.

        Args:
            course (CourseDescriptor): the course using the feature
            user (User): the user interacting with the course
        """
        if not super(TeamsTab, cls).is_enabled(course, user=user):
            return False

        return is_feature_enabled(course)
