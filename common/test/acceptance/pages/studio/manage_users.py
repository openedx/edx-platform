"""
Course Team page in Studio.
"""

from .course_page import CoursePage


class CourseTeamPage(CoursePage):
    """
    Course Team page in Studio.
    """

    url_path = "course_team"

    def is_browser_on_page(self):
        return self.q(css='body.view-team').present
