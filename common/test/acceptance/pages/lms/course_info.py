"""
Course info page.
"""

from common.test.acceptance.pages.lms.course_page import CoursePage


class CourseInfoPage(CoursePage):
    """
    Course info.
    """

    url_path = "info"

    def is_browser_on_page(self):
        return self.q(css='section.updates').present

    @property
    def num_updates(self):
        """
        Return the number of updates on the page.
        """
        return len(self.q(css='.updates .updates-article').results)

    @property
    def handout_links(self):
        """
        Return a list of handout assets links.
        """
        return self.q(css='section.handouts ol li a').map(lambda el: el.get_attribute('href')).results
