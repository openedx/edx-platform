"""
Registers the CCX feature for the edX platform.
"""

from django.utils.translation import ugettext as _

from openedx.core.djangoapps.course_views.course_views import CourseViewType


class CcxCourseViewType(CourseViewType):
    """
    The representation of the CCX course view type.
    """

    name = "ccx_coach"
    title = _("CCX Coach")
    view_name = "ccx_coach_dashboard"
    is_dynamic = True    # The CCX view is dynamically added to the set of tabs when it is enabled

    @classmethod
    def is_enabled(cls, course, settings, user=None):
        """
        Returns true if CCX has been enabled and the specified user is a coach
        """
        if not user or not settings.FEATURES.get('CUSTOM_COURSES_EDX', False):
            return False
        from student.roles import CourseCcxCoachRole  # pylint: disable=import-error
        role = CourseCcxCoachRole(course.id)
        return role.has_user(user)
