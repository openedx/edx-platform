"""
Platform plugins to support the course experience.

This includes any locally defined CourseTools.
"""
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

from course_tools import CourseTool
from courseware.courses import get_course_by_id
from views.course_reviews import CourseReviewsModuleFragmentView
from views.course_updates import CourseUpdatesFragmentView

from . import SHOW_REVIEWS_TOOL_FLAG, UNIFIED_COURSE_TAB_FLAG


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
    def is_enabled(cls, request, course_key):
        """
        Returns True if this tool is enabled for the specified course key.
        """
        course = get_course_by_id(course_key)
        has_updates = CourseUpdatesFragmentView.has_updates(request, course)
        return UNIFIED_COURSE_TAB_FLAG.is_enabled(course_key) and has_updates

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
    def is_enabled(cls, request, course_key):
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
