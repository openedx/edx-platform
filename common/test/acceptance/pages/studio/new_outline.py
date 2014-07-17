"""
Course Outline page in Studio.
"""
from bok_choy.page_object import PageObject
from bok_choy.promise import EmptyPromise

from .course_page import CoursePage
from .container import ContainerPage
from .utils import set_input_value_and_save


class NewCourseOutlinePage(CoursePage):
    """
    Course Outline page in Studio.
    """
    url_path = "course"

    def is_browser_on_page(self):
        return self.q(css='body.view-outline').present

    def edit_section(self):
        self.q(css=".icon-gear").first.click()

    def edit_subsection(self):
        self.q(css=".icon-gear").nth(1).click()

    def modal_is_shown(self):
        self.q(css=".edit-xblock-modal").present

    def press_cancel_on_modal(self):
        self.q(css=".action-cancel").present
        self.q(css=".action-cancel").first.click()

    def press_save_on_modal(self):
        self.q(css=".action-save").present
        self.q(css=".action-save").first.click()
