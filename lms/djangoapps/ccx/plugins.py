"""
Registers the CCX feature for the edX platform.
"""


from django.conf import settings
from django.utils.translation import gettext_noop

from common.djangoapps.student.auth import is_ccx_course
from common.djangoapps.student.roles import CourseCcxCoachRole
from xmodule.tabs import CourseTab  # lint-amnesty, pylint: disable=wrong-import-order

from .permissions import VIEW_CCX_COACH_DASHBOARD

from openedx_filters.license_enforcement.filters import (
    CourseLicensingEnabledRequested,
    CcxCreationPermissionRequested,
)


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

        # If Course Licensing is enabled, disable CCXCoach tab for master courses if user is not allowed to create ccx.
        is_course_licensing_enabled = CourseLicensingEnabledRequested.run_filter(enabled=False)

        if (
            not is_ccx_course(course.id) and
            is_course_licensing_enabled and
            not CcxCreationPermissionRequested.run_filter(
                user=user,
                master_course=course.id,
                allowed=False,
            )
        ):
            # If course licensing is enable, then regular ccxs are disabled.
            return False

        if hasattr(course.id, 'ccx') and bool(user.has_perm(VIEW_CCX_COACH_DASHBOARD, course)):
            return True

        # check if user has coach access.
        role = CourseCcxCoachRole(course.id)
        return role.has_user(user)
