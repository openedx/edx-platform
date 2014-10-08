"""
My Courses page in Studio
"""

from bok_choy.page_object import PageObject
from . import BASE_URL


class DashboardPage(PageObject):
    """
    My Courses page in Studio
    """

    url = BASE_URL + "/course/"

    def is_browser_on_page(self):
        return self.q(css='body.view-dashboard').present

    @property
    def has_processing_courses(self):
        return self.q(css='.courses-processing').present

    def create_rerun(self, display_name):
        """
        Clicks the create rerun link of the course specified by display_name.
        """
        name = self.q(css='.course-title').filter(lambda el: el.text == display_name)[0]
        name.find_elements_by_xpath('../..')[0].find_elements_by_class_name('rerun-button')[0].click()

    def click_course_run(self, run):
        """
        Clicks on the course with run given by run.
        """
        self.q(css='.course-run .value').filter(lambda el: el.text == run)[0].click()
