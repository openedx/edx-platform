"""
Course rerun page in Studio
"""

from .course_page import CoursePage
from .utils import set_input_value


class CourseRerunPage(CoursePage):
    """
    Course rerun page in Studio
    """

    url_path = "course_rerun"
    COURSE_RUN_INPUT = '.rerun-course-run'

    def is_browser_on_page(self):
        """
        Returns True iff the browser has loaded the course rerun page.
        """
        return self.q(css='body.view-course-create-rerun').present

    @property
    def course_run(self):
        """
        Returns the value of the course run field.
        """
        return self.q(css=self.COURSE_RUN_INPUT).text[0]

    @course_run.setter
    def course_run(self, value):
        """
        Sets the value of the course run field.
        """
        set_input_value(self, self.COURSE_RUN_INPUT, value)

    def create_rerun(self):
        """
        Clicks the create rerun button.
        """
        self.q(css='.rerun-course-save')[0].click()
        # Clicking on the course will trigger an ajax event
        self.wait_for_ajax()
