"""
Course Checklists page.
"""

from common.test.acceptance.pages.studio.course_page import CoursePage


class CourseChecklistsPage(CoursePage):
    """
    Course Checklists page.
    """

    url_path = "checklists"

    def is_browser_on_page(self):
        # SFE and SFE-wrapper classes come from studio-frontend and
        # wrap content provided by the studio-frontend package
        return self.q(css='.SFE .SFE-wrapper').visible
