"""
The Files and Uploads page for a course in Studio
"""

from .course_page import CoursePage


class AssetIndexPage(CoursePage):
    """
    The Files and Uploads page for a course in Studio
    """

    url_path = "assets"

    def is_browser_on_page(self):
        return self.q(css='body.view-uploads').present
