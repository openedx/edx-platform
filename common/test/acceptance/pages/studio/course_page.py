"""
Base class for pages specific to a course in Studio.
"""

from bok_choy.page_object import PageObject
from . import BASE_URL


class CoursePage(PageObject):
    """
    Abstract base class for page objects specific to a course in Studio.
    """

    # Overridden by subclasses to provide the relative path within the course
    # Does not need to include the leading forward or trailing slash
    url_path = ""

    def __init__(self, browser, course_org, course_num, course_run):
        """
        Initialize the page object for the course located at
        `{course_org}.{course_num}.{course_run}`

        These identifiers will likely change in the future.
        """
        super(CoursePage, self).__init__(browser)
        self.course_info = {
            'course_org': course_org,
            'course_num': course_num,
            'course_run': course_run
        }

    @property
    def url(self):
        """
        Construct a URL to the page within the course.
        """
        course_key = "{course_org}/{course_num}/{course_run}".format(**self.course_info)
        return "/".join([BASE_URL, self.url_path, course_key])
