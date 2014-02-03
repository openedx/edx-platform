"""
Course info page.
"""

from .course_page import CoursePage


class CourseInfoPage(CoursePage):
    """
    Course info.
    """

    URL_PATH = "info"

    def is_browser_on_page(self):
        return self.is_css_present('section.updates')

    @property
    def num_updates(self):
        """
        Return the number of updates on the page.
        """
        return self.css_count('section.updates ol li')

    @property
    def handout_links(self):
        """
        Return a list of handout assets links.
        """
        return self.css_map('section.handouts ol li a', lambda el: el['href'])
