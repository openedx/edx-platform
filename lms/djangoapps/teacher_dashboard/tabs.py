"""
Registers Teacher Dashboard for the edX platform.
"""
from django.utils.translation import ugettext_noop
from xmodule.tabs import CourseTab
from teacher_dashboard.utils import has_teacher_access


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
        Indicates whether the tab needs to be shown.
        """
        return has_teacher_access(user, course)
