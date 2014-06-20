"""
Courseware page.
"""

from .course_page import CoursePage


class CoursewarePage(CoursePage):
    """
    Course info.
    """

    url_path = "courseware/"

    def is_browser_on_page(self):
        return self.q(css='body.courseware').present
