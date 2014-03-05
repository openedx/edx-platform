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
        return self.q(css='body.view-checklists').present
