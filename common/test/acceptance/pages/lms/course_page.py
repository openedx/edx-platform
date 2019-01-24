"""
Base class for pages in courseware.
"""

from bok_choy.page_object import PageObject

from common.test.acceptance.pages.lms import BASE_URL
from common.test.acceptance.pages.lms.tab_nav import TabNavPage


class CoursePage(PageObject):
    """
    Abstract base class for page objects within a course.
    """

    # Overridden by subclasses to provide the relative path within the course
    # Paths should not include the leading forward slash.
    url_path = ""

    def __init__(self, browser, course_id):
        """
        Course ID is currently of the form "edx/999/2013_Spring"
        but this format could change.
        """
        super(CoursePage, self).__init__(browser)
        self.course_id = course_id

    @property
    def url(self):
        """
        Construct a URL to the page within the course.
        """
        return BASE_URL + "/courses/" + self.course_id + "/" + self.url_path

    def has_tab(self, tab_name):
        """
        Returns true if the current page is showing a tab with the given name.
        :return:
        """
        tab_nav = TabNavPage(self.browser)
        return tab_name in tab_nav.tab_names

    def wait_for_mathjax(self, timeout=15):
        """
        Wait for the MathJax startup files to load, unless the timeout occurs.
        """
        def has_mathjax_loaded():
            """
            Checks if the MathJax startup sequence has completed.
            """
            return self.browser.execute_script(
                "return typeof(MathJax)!='undefined' && MathJax.isReady==true"
            )

        self.wait_for(
            promise_check_func=has_mathjax_loaded,
            description='Waiting to load MathJax',
            timeout=timeout
        )

    def wait_for_mathjax_operations(self, timeout=10):
        """
        Wait for the MathJax operations to complete, unless the timeout occurs.
        """
        def have_mathjax_operations_completed():
            """
            Checks if the MathJax hub queue has any running and pending operations.
            """
            return self.browser.execute_script(
                "return MathJax.Hub.queue.running==0 && MathJax.Hub.queue.queue.length==0"
                " && MathJax.Hub.queue.pending==0"
            )
        self.wait_for(
            promise_check_func=have_mathjax_operations_completed,
            description='Waiting for MathJax Operations to finish',
            timeout=timeout
        )
