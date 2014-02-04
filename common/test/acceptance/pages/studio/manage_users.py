"""
Course Team page in Studio.
"""

from .course_page import CoursePage


class CourseTeamPage(CoursePage):
    """
    Course Team page in Studio.
    """

    URL_PATH = "course_team"

    def is_browser_on_page(self):
        return self.is_css_present('body.view-team')
