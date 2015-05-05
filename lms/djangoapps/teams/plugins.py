"""
Definition of the course team feature.
"""

from django.utils.translation import ugettext as _


class TeamsCourseViewType(object):
    """
    The representation of the course teams view type.
    """

    name = "edx.teams"
    title = _("Teams")
    view_name = "teams_dashboard"
    is_persistent = True

    @classmethod
    def is_enabled(cls, course, settings, user=None):  # pylint: disable=unused-argument
        """Returns true if the teams feature is enabled in the course.

        Args:
            course (CourseDescriptor): the course using the feature
            settings (dict): a dict of configuration settings
            user (User): the user interacting with the course
        """
        # TODO: the tab is only enabled if at least one team topic is defined
        return not user or settings.FEATURES.get('ENABLE_TEAMS', False)
