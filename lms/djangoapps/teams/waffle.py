"""
Togglable settings for Teams behavior
"""
from django.conf import settings
from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag


# Course Waffle inherited from edx/edx-ora2
WAFFLE_NAMESPACE = 'openresponseassessment'
TEAM_SUBMISSIONS_FLAG = 'team_submissions'

# edx/edx-platform feature
TEAM_SUBMISSIONS_FEATURE = 'ENABLE_ORA_TEAM_SUBMISSIONS'


def are_team_submissions_enabled(course_key):
    """
    Checks to see if the CourseWaffleFlag or Django setting for team submissions is enabled
    """
    if CourseWaffleFlag(WAFFLE_NAMESPACE, TEAM_SUBMISSIONS_FLAG, __name__).is_enabled(course_key):
        return True

    if settings.FEATURES.get(TEAM_SUBMISSIONS_FEATURE, False):
        return True

    return False
