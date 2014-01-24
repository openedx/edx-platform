"""
Course Grading Settings page.
"""

from bok_choy.page_object import PageObject
from .helpers import parse_course_id
from . import BASE_URL


class GradingPage(PageObject):
    """
    Course Grading Settings page.
    """

    name = "studio.grading"

    def url(self, course_id=None):  #pylint: disable=W0221
        """
        URL for the course team page of a course.
        `course_id` is a string of the form "org.number.run" and is required.
        """
        _, _, course_run = parse_course_id(course_id)

        return "{0}/settings/grading/{1}/branch/draft/block/{2}".format(
            BASE_URL, course_id, course_run
        )

    def is_browser_on_page(self):
        return self.is_css_present('body.grading')
