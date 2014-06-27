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

    @property
    def xblock_component_type(self):
        """
        Extract rendered xblock component type.

        Returns:
            str: xblock module type

        """
        xblock_component_selector = '.vert .xblock'
        return self.q(css=xblock_component_selector).attrs('data-block-type')[0]

    @property
    def xblock_component_html_content(self):
        """
        Extract rendered xblock component html content.

        Returns:
            str: xblock module html content

        """
        xblock_component_selector = '.vert .xblock'
        return self.q(css=xblock_component_selector).attrs('innerHTML')[0].strip()
