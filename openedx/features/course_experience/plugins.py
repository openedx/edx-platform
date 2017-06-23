"""
Platform plugins to support the course experience.

This includes any locally defined CourseTools.
"""

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

from . import UNIFIED_COURSE_TAB_FLAG, SHOW_REVIEWS_TOOL_FLAG
from views.course_reviews import CourseReviewsModuleFragmentView
from course_tools import CourseTool


class CourseUpdatesTool(CourseTool):
    """
    The course updates tool.
    """
    @classmethod
    def title(cls):
        """
        Returns the title of this tool.
        """
        return _('Updates')

    @classmethod
    def icon_classes(cls):
        """
        Returns icon classes needed to represent this tool.
        """
        return 'fa fa-newspaper-o'

    @classmethod
    def is_enabled(cls, course_key):
        """
        Returns True if this tool is enabled for the specified course key.
        """
        return UNIFIED_COURSE_TAB_FLAG.is_enabled(course_key)

    @classmethod
    def url(cls, course_key):
        """
        Returns the URL for this tool for the specified course key.
        """
        return reverse('openedx.course_experience.course_updates', args=[course_key])


class CourseReviewsTool(CourseTool):
    """
    The course reviews tool.
    """
    @classmethod
    def title(cls):
        """
        Returns the title of this tool.
        """
        return _('Reviews')

    @classmethod
    def icon_classes(cls):
        """
        Returns icon classes needed to represent this tool.
        """
        return 'fa fa-star'

    @classmethod
    def is_enabled(cls, course_key):
        """
        Returns True if this tool is enabled for the specified course key.
        """
        reviews_configured = CourseReviewsModuleFragmentView.is_configured()
        return SHOW_REVIEWS_TOOL_FLAG.is_enabled(course_key) and reviews_configured

    @classmethod
    def url(cls, course_key):
        """
        Returns the URL for this tool for the specified course key.
        """
        return reverse('openedx.course_experience.course_reviews', args=[course_key])
