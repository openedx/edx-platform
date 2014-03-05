"""
Course checklists page.
"""

from .course_page import CoursePage


class ChecklistsPage(CoursePage):
    """
    Course Checklists page.
    """

    url_path = "checklists"

    def is_browser_on_page(self):
        return self.is_css_present('body.view-checklists')
