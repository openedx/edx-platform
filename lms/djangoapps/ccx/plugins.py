"""
Registers the CCX feature for the edX platform.
"""

from django.utils.translation import ugettext as _

from openedx.core.lib.plugins.api import CourseViewType
from student.roles import CourseCcxCoachRole


class CcxCourseViewType(CourseViewType):
    """
    The representation of the CCX course view type.
    """

    name = "ccx_coach"
    title = _("CCX Coach")
    view_name = "ccx_coach_dashboard"
    is_persistent = False

    @classmethod
    def is_enabled(cls, course, settings, user=None):
        """
        Returns true if CCX has been enabled and the specified user is a coach
        """
        if not user:
            return True
        if not settings.FEATURES.get('CUSTOM_COURSES_EDX', False) or not course.enable_ccx:
            return False
        role = CourseCcxCoachRole(course.id)
        return role.has_user(user)
