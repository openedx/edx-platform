"""
Registers Teacher Dashboard for the edX platform.
"""
from django.conf import settings
from django.utils.translation import ugettext_noop
from xmodule.tabs import CourseTab
from courseware.access import has_access


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
        is_feature_enabled = settings.LABSTER_FEATURES.get('ENABLE_TEACHER_DASHBOARD', False)
        return bool(user and has_access(user, 'staff', course, course.id)) and is_feature_enabled
