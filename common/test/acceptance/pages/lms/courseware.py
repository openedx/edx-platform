"""
Courseware page.
"""

from .course_page import CoursePage


class CoursewarePage(CoursePage):
    """
    Course info.
    """

    url_path = "courseware/"
    xblock_component_selector = '.vert .xblock'

    def is_browser_on_page(self):
        return self.q(css='body.courseware').present

    @property
    def num_xblock_components(self):
        """
        Return the number of rendered xblocks within the unit on the page
        """
        return len(self.q(css=self.xblock_component_selector))

    def xblock_component_type(self, index=0):
        """
        Extract rendered xblock component type.

        Returns:
            str: xblock module type
            index: which xblock to query, where the index is the vertical display within the page
                (default is 0)
        """
        return self.q(css=self.xblock_component_selector).attrs('data-block-type')[index]

    def xblock_component_html_content(self, index=0):
        """
        Extract rendered xblock component html content.

        Returns:
            str: xblock module html content
            index: which xblock to query, where the index is the vertical display within the page
                (default is 0)

        """
        return self.q(css=self.xblock_component_selector).attrs('innerHTML')[index].strip()
