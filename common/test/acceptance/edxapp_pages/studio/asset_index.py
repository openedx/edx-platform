"""
The Files and Uploads page for a course in Studio
"""

from .course_page import CoursePage


class AssetIndexPage(CoursePage):
    """
    The Files and Uploads page for a course in Studio
    """

    URL_PATH = "assets"

    def is_browser_on_page(self):
        return self.is_css_present('body.view-uploads')
