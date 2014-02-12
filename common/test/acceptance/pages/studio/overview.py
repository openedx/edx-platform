"""
Course Outline page in Studio.
"""

from .course_page import CoursePage


class CourseOutlinePage(CoursePage):
    """
    Course Outline page in Studio.
    """

    url_path = "course"

    def is_browser_on_page(self):
        return self.is_css_present('body.view-outline')
