"""
Platform plugins to support course bookmarks.
"""

from courseware.access import has_access
from django.urls import reverse
from django.utils.translation import ugettext as _
from openedx.features.course_experience.course_tools import CourseTool
from student.models import CourseEnrollment


class CourseBookmarksTool(CourseTool):
    """
    The course bookmarks tool.
    """
    @classmethod
    def analytics_id(cls):
        """
        Returns an id to uniquely identify this tool in analytics events.
        """
        return 'edx.bookmarks'

    @classmethod
    def is_enabled(cls, request, course_key):
        """
        The bookmarks tool is only enabled for enrolled users or staff.
        """
        if has_access(request.user, 'staff', course_key):
            return True
        return CourseEnrollment.is_enrolled(request.user, course_key)

    @classmethod
    def title(cls):
        """
        Returns the title of this tool.
        """
        return _('Bookmarks')

    @classmethod
    def icon_classes(cls):
        """
        Returns the icon classes needed to represent this tool.
        """
        return 'fa fa-bookmark'

    @classmethod
    def url(cls, course_key):
        """
        Returns the URL for this tool for the specified course key.
        """
        return reverse('openedx.course_bookmarks.home', args=[course_key])
