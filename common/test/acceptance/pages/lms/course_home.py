"""
LMS Course Home page object
"""

from bok_choy.page_object import PageObject

from common.test.acceptance.pages.lms.course_page import CoursePage
from common.test.acceptance.pages.lms.courseware import CoursewarePage


class CourseHomePage(CoursePage):
    """
    Course home page, including course outline.
    """

    url_path = "course/"

    def is_browser_on_page(self):
        return self.q(css='.course-outline').present

    def __init__(self, browser, course_id):
        super(CourseHomePage, self).__init__(browser, course_id)
        self.course_id = course_id
        self.outline = CourseOutlinePage(browser, self)
        # TODO: TNL-6546: Remove the following
        self.unified_course_view = False


class CourseOutlinePage(PageObject):
    """
    Course outline fragment of page.
    """

    url = None

    def __init__(self, browser, parent_page):
        super(CourseOutlinePage, self).__init__(browser)
        self.parent_page = parent_page
        self.courseware_page = CoursewarePage(self.browser, self.parent_page.course_id)

    def is_browser_on_page(self):
        return self.parent_page.is_browser_on_page

    @property
    def sections(self):
        """
        Return a dictionary representation of sections and subsections.

        Example:

            {
                'Introduction': ['Course Overview'],
                'Week 1': ['Lesson 1', 'Lesson 2', 'Homework']
                'Final Exam': ['Final Exam']
            }

        You can use these titles in `go_to_section` to navigate to the section.
        """
        # Dict to store the result
        outline_dict = dict()

        section_titles = self._section_titles()

        # Get the section titles for each chapter
        for sec_index, sec_title in enumerate(section_titles):

            if len(section_titles) < 1:
                self.warning("Could not find subsections for '{0}'".format(sec_title))
            else:
                # Add one to convert list index (starts at 0) to CSS index (starts at 1)
                outline_dict[sec_title] = self._subsection_titles(sec_index + 1)

        return outline_dict

    def go_to_section(self, section_title, subsection_title):
        """
        Go to the section in the courseware.
        Every section must have at least one subsection, so specify
        both the section and subsection title.

        Example:
            go_to_section("Week 1", "Lesson 1")
        """

        # Get the section by index
        try:
            section_index = self._section_titles().index(section_title)
        except ValueError:
            self.warning("Could not find section '{0}'".format(section_title))
            return

        # Get the subsection by index
        try:
            subsection_index = self._subsection_titles(section_index + 1).index(subsection_title)
        except ValueError:
            msg = "Could not find subsection '{0}' in section '{1}'".format(subsection_title, section_title)
            self.warning(msg)
            return

        # Convert list indices (start at zero) to CSS indices (start at 1)
        subsection_css = (
            ".outline-item.section:nth-of-type({0}) .subsection:nth-of-type({1}) .outline-item"
        ).format(section_index + 1, subsection_index + 1)

        # Click the subsection and ensure that the page finishes reloading
        self.q(css=subsection_css).first.click()
        self.courseware_page.wait_for_page()

        # TODO: TNL-6546: Remove this if/visit_unified_course_view
        if self.parent_page.unified_course_view:
            self.courseware_page.nav.visit_unified_course_view()

        self._wait_for_course_section(section_title, subsection_title)

    def _section_titles(self):
        """
        Return a list of all section titles on the page.
        """
        section_css = '.section-name span'
        return self.q(css=section_css).map(lambda el: el.text.strip()).results

    def _subsection_titles(self, section_index):
        """
        Return a list of all subsection titles on the page
        for the section at index `section_index` (starts at 1).
        """
        # Retrieve the subsection title for the section
        # Add one to the list index to get the CSS index, which starts at one
        subsection_css = (
            # TODO: TNL-6387: Will need to switch to this selector for subsections
            # ".outline-item.section:nth-of-type({0}) .subsection span:nth-of-type(1)"
            ".outline-item.section:nth-of-type({0}) .subsection a"
        ).format(section_index)

        return self.q(
            css=subsection_css
        ).map(
            lambda el: el.get_attribute('innerHTML').strip()
        ).results

    def _wait_for_course_section(self, section_title, subsection_title):
        """
        Ensures the user navigates to the course content page with the correct section and subsection.
        """
        self.wait_for(
            promise_check_func=lambda: self.courseware_page.nav.is_on_section(section_title, subsection_title),
            description="Waiting for course page with section '{0}' and subsection '{1}'".format(section_title, subsection_title)
        )
