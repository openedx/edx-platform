"""
Registers the Labster Course License for the edX platform.
"""

from django.conf import settings
from django.utils.translation import ugettext_noop

from xmodule.tabs import CourseTab
from student.roles import CourseCcxCoachRole
from courseware.access import has_access


class LicenseCourseTab(CourseTab):
    """
    The representation of the LTI Passport course tab
    """

    type = "course_license"
    title = ugettext_noop("License")
    view_name = "labster_license_handler"
    is_dynamic = True

    @classmethod
    def is_enabled(cls, course, user=None):
        """
        Returns true if CCX has been enabled and the specified user is a coach
        """
        if not settings.FEATURES.get('CUSTOM_COURSES_EDX', False) or not course.enable_ccx:
            # If ccx is not enable do not show License tab.
            return False

        if has_access(user, 'staff', course) or has_access(user, 'instructor', course):
            # if user is staff or instructor then he can always see License tab.
            return True

        role = CourseCcxCoachRole(course.id)
        return role.has_user(user)
