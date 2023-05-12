"""
Registers the CCX feature for the edX platform.
"""


from django.conf import settings
from django.utils.translation import gettext_noop
from openedx.core.djangoapps.plugins.plugins_hooks import run_extension_point
from common.djangoapps.student.auth import is_ccx_course

from common.djangoapps.student.roles import CourseCcxCoachRole
from xmodule.tabs import CourseTab  # lint-amnesty, pylint: disable=wrong-import-order

from .permissions import VIEW_CCX_COACH_DASHBOARD


class CcxCourseTab(CourseTab):
    """
    The representation of the CCX course tab
    """

    type = "ccx_coach"
    priority = 310
    title = gettext_noop("CCX Coach")
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

        # If Course Licensing is enable, disable CCXCoach tab for master courses if user is not allowed to create ccx.
        is_course_licensing_enabled = run_extension_point('PCO_ENABLE_COURSE_LICENSING')

        if (
            not is_ccx_course(course.id) and
            is_course_licensing_enabled and
            not run_extension_point(
                'PCO_IS_USER_ALLOWED_TO_CREATE_CCX',
                user=user,
                master_course=course.id,
            )
        ):
            # If course licensing is enable, then regular ccxs are disabled.
            return False

        if hasattr(course.id, 'ccx') and bool(user.has_perm(VIEW_CCX_COACH_DASHBOARD, course)):
            return True

        # check if user has coach access.
        role = CourseCcxCoachRole(course.id)
        return role.has_user(user)
