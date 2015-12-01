"""
Registers the CCX feature for the edX platform.
"""

from django.conf import settings
from django.utils.translation import ugettext_noop

from xmodule.tabs import CourseTab
from student.roles import CourseCcxCoachRole


class CcxCourseTab(CourseTab):
    """
    The representation of the CCX course tab
    """

    type = "ccx_coach"
    title = ugettext_noop("CCX Coach")
    view_name = "ccx_coach_dashboard"
    is_dynamic = True    # The CCX view is dynamically added to the set of tabs when it is enabled

    @classmethod
    def is_enabled(cls, course, user=None):
        """
        Returns true if CCX has been enabled and the specified user is a coach
        """
        if not user:
            return True
        if not settings.FEATURES.get('CUSTOM_COURSES_EDX', False) or not course.enable_ccx:
            return False
        role = CourseCcxCoachRole(course.id)
        return role.has_user(user)
