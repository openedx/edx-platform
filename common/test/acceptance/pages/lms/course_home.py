"""
LMS Course Home page object
"""


from .course_page import CoursePage
from .staff_view import StaffPreviewPage


class CourseHomePage(CoursePage):
    """
    Course home page, including course outline.
    """

    url_path = "course/"

    HEADER_RESUME_COURSE_SELECTOR = '.page-header .action-resume-course'

    def is_browser_on_page(self):
        return self.q(css='.course-outline').present

    def __init__(self, browser, course_id):
        super(CourseHomePage, self).__init__(browser, course_id)
        self.course_id = course_id
        self.preview = StaffPreviewPage(browser, self)
        # TODO: TNL-6546: Remove the following
        self.course_outline_page = False
