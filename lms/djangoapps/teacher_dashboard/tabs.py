"""
Registers Teacher Dashboard for the edX platform.
"""
from django.conf import settings
from django.utils.translation import ugettext_noop
from xmodule.tabs import CourseTab
from courseware.access import has_access
from ccx.utils import get_ccx_from_ccx_locator
from student.roles import CourseCcxCoachRole


class TeacherDashboardTab(CourseTab):
    """
    The representation of the Teacher Dashboard
    """

    type = "teacher_dashboard"
    title = ugettext_noop("Teacher Dashboard")
    view_name = "dashboard_view_handler"
    is_dynamic = True

    @classmethod
    def is_enabled(cls, course, user=None):
        """
        Returns True when:
            Teached dashboard feature is enabled
            AND (
                user has staff role
                OR (
                    CCX feature is enabled AND user has coach role
                )
            )
        """
        if not (user and settings.LABSTER_FEATURES.get('ENABLE_TEACHER_DASHBOARD', False)):
            return False

        # Displays tab for course staff.
        if bool(has_access(user, 'staff', course, course.id)):
            return True

        # The tab is hidden if the user is not staff and CCX feature is disabled.
        if not (settings.FEATURES.get('CUSTOM_COURSES_EDX', False) and course.enable_ccx):
            return False

        ccx = get_ccx_from_ccx_locator(course.id)
        if ccx:
            return CourseCcxCoachRole(ccx.course_id).has_user(user)

        return False
