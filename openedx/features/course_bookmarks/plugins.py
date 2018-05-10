"""
Platform plugins to support course bookmarks.
"""

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from openedx.features.course_experience.course_tools import CourseTool


class CourseBookmarksTool(CourseTool):
    """
    The course bookmarks tool.
    """
    @classmethod
    def is_enabled(cls, request, course_key):
        """
        Always show the bookmarks tool.
        """
        return True

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
