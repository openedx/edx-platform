from courseware.tabs import CourseTab
from django.utils.translation import ugettext_noop


class NewCourseNavTab(CourseTab):
    """
    Defines the new course navigation tab.
    """

    name = "new_course_nav"
    type = "new_course_nav"
    title = ugettext_noop("New Course Navigation")
    view_name = "new_course_nav"

    @classmethod
    def is_enabled(cls, course, user=None):
        """Returns true if this tab is enabled."""
        return True
