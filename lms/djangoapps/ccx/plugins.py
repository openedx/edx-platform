"""
Registers the CCX feature for the edX platform.
"""

from django.conf import settings
from django.utils.translation import ugettext_noop

from xmodule.tabs import CourseTab
from student.roles import CourseCcxCoachRole
from courseware.access import has_access


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
        if not settings.FEATURES.get('CUSTOM_COURSES_EDX', False) or not course.enable_ccx:
            # If ccx is not enable do not show ccx coach tab.
            return False
        if has_access(user, 'staff', course) or has_access(user, 'instructor', course):
            # if user is staff or instructor then he can always see ccx coach tab.
            return True
        # check if user has coach access.
        role = CourseCcxCoachRole(course.id)
        return role.has_user(user)
