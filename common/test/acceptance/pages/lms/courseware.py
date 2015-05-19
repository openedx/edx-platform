"""
Courseware page.
"""

from .course_page import CoursePage
from selenium.webdriver.common.action_chains import ActionChains


class CoursewarePage(CoursePage):
    """
    Course info.
    """

    url_path = "courseware/"
    xblock_component_selector = '.vert .xblock'
    section_selector = '.chapter'
    subsection_selector = '.chapter ul li'

    def is_browser_on_page(self):
        return self.q(css='body.courseware').present

    @property
    def num_sections(self):
        """
        Return the number of sections in the sidebar on the page
        """
        return len(self.q(css=self.section_selector))

    @property
    def num_subsections(self):
        """
        Return the number of subsections in the sidebar on the page, including in collapsed sections
        """
        return len(self.q(css=self.subsection_selector))

    @property
    def xblock_components(self):
        """
        Return the xblock components within the unit on the page.
        """
        return self.q(css=self.xblock_component_selector)

    @property
    def num_xblock_components(self):
        """
        Return the number of rendered xblocks within the unit on the page
        """
        return len(self.xblock_components)

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
        # When Student Notes feature is enabled, it looks for the content inside
        # `.edx-notes-wrapper-content` element (Otherwise, you will get an
        # additional html related to Student Notes).
        element = self.q(css='{} .edx-notes-wrapper-content'.format(self.xblock_component_selector))
        if element.first:
            return element.attrs('innerHTML')[index].strip()
        else:
            return self.q(css=self.xblock_component_selector).attrs('innerHTML')[index].strip()

    def tooltips_displayed(self):
        """
        Verify if sequence navigation bar tooltips are being displayed upon mouse hover.
        """
        for index, tab in enumerate(self.q(css='#sequence-list > li')):
            ActionChains(self.browser).move_to_element(tab).perform()
            if not self.q(css='#tab_{index} > p'.format(index=index)).visible:
                return False

        return True

    @property
    def course_license(self):
        """
        Returns the course license text, if present. Else returns None.
        """
        element = self.q(css="#content .container-footer .course-license")
        if element.is_present():
            return element.text[0]
        return None

    def get_active_subsection_url(self):
        """
        return the url of the active subsection in the left nav
        """
        return self.q(css='.chapter ul li.active a').attrs('href')[0]


class CoursewareSequentialTabPage(CoursePage):
    """
    Courseware Sequential page
    """

    def __init__(self, browser, course_id, chapter, subsection, position):
        super(CoursewareSequentialTabPage, self).__init__(browser, course_id)
        self.url_path = "courseware/{}/{}/{}".format(chapter, subsection, position)

    def is_browser_on_page(self):
        return self.q(css='nav.sequence-list-wrapper').present

    def get_selected_tab_content(self):
        """
        return the body of the sequential currently selected
        """
        return self.q(css='#seq_content .xblock').text[0]
