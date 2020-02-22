"""
Base class for pages specific to a course in Studio.
"""


import os
from abc import abstractmethod

import six
from bok_choy.page_object import PageObject
from opaque_keys.edx.locator import CourseLocator

from common.test.acceptance.pages.studio import BASE_URL
from common.test.acceptance.pages.studio.utils import HelpMixin


class CoursePage(PageObject, HelpMixin):
    """
    Abstract base class for page objects specific to a course in Studio.
    """

    # Overridden by subclasses to provide the relative path within the course
    # Does not need to include the leading forward or trailing slash
    url_path = ""

    @abstractmethod
    def is_browser_on_page(self):
        """
        Verifies browser is on the correct page.

        Should be implemented in child classes.
        """
        pass

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
        # TODO - is there a better way to make this agnostic to the underlying default module store?
        default_store = os.environ.get('DEFAULT_STORE', 'draft')
        course_key = CourseLocator(
            self.course_info['course_org'],
            self.course_info['course_num'],
            self.course_info['course_run'],
            deprecated=(default_store == 'draft')
        )
        return "/".join([BASE_URL, self.url_path, six.text_type(course_key)])
