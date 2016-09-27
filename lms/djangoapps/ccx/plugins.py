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
        # Start: Added By Labster
        # Hide the tab in CCX becasue it missleads to master course.
        # This fix has to be removed after upgrading to Eucalyptus.
        ccx_id = getattr(course.id, 'ccx', None)
        if ccx_id is not None:
            return False
        # End: Added By Labster
        role = CourseCcxCoachRole(course.id)
        return role.has_user(user)
