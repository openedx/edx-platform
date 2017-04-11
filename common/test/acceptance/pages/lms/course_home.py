"""
LMS Course Home page object
"""

from collections import OrderedDict
from bok_choy.page_object import PageObject

from .bookmarks import BookmarksPage
from .course_page import CoursePage
from .courseware import CoursewarePage
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
        self.outline = CourseOutlinePage(browser, self)
        self.preview = StaffPreviewPage(browser, self)
        # TODO: TNL-6546: Remove the following
        self.unified_course_view = False

    def click_bookmarks_button(self):
        """ Click on Bookmarks button """
        self.q(css='.bookmarks-list-button').first.click()
        bookmarks_page = BookmarksPage(self.browser, self.course_id)
        bookmarks_page.visit()

    def resume_course_from_header(self):
        """
        Navigate to courseware using Resume Course button in the header.
        """
        self.q(css=self.HEADER_RESUME_COURSE_SELECTOR).first.click()
        courseware_page = CoursewarePage(self.browser, self.course_id)
        courseware_page.wait_for_page()


class CourseOutlinePage(PageObject):
    """
    Course outline fragment of page.
    """

    url = None

    SECTION_SELECTOR = '.outline-item.section:nth-of-type({0})'
    SECTION_TITLES_SELECTOR = '.section-name h3'
    SUBSECTION_SELECTOR = SECTION_SELECTOR + ' .subsection:nth-of-type({1}) .outline-item'
    SUBSECTION_TITLES_SELECTOR = SECTION_SELECTOR + ' .subsection .subsection-title'
    OUTLINE_RESUME_COURSE_SELECTOR = '.outline-item .resume-right'

    def __init__(self, browser, parent_page):
        super(CourseOutlinePage, self).__init__(browser)
        self.parent_page = parent_page

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
        outline_dict = OrderedDict()

        section_titles = self._section_titles()

        # Get the section titles for each chapter
        for sec_index, sec_title in enumerate(section_titles):

            if len(section_titles) < 1:
                raise ValueError("Could not find subsections for '{0}'".format(sec_title))
            else:
                # Add one to convert list index (starts at 0) to CSS index (starts at 1)
                outline_dict[sec_title] = self._subsection_titles(sec_index + 1)

        return outline_dict

    @property
    def num_sections(self):
        """
        Return the number of sections
        """
        return len(self.q(css=self.SECTION_TITLES_SELECTOR))

    @property
    def num_subsections(self, section_title=None):
        """
        Return the number of subsections.

        Arguments:
            section_title: The section for which to return the number of
                subsections. If None, default to the first section.
        """
        if section_title:
            section_index = self._section_title_to_index(section_title)
            if not section_index:
                return
        else:
            section_index = 1

        return len(self.q(css=self.SUBSECTION_TITLES_SELECTOR.format(section_index)))

    def go_to_section(self, section_title, subsection_title):
        """
        Go to the section/subsection in the courseware.
        Every section must have at least one subsection, so specify
        both the section and subsection title.

        Example:
            go_to_section("Week 1", "Lesson 1")
        """
        section_index = self._section_title_to_index(section_title)
        if section_index is None:
            raise ValueError("Could not find section '{0}'".format(section_title))

        try:
            subsection_index = self._subsection_titles(section_index + 1).index(subsection_title)
        except ValueError:
            raise ValueError("Could not find subsection '{0}' in section '{1}'".format(
                subsection_title, section_title
            ))

        # Convert list indices (start at zero) to CSS indices (start at 1)
        subsection_css = self.SUBSECTION_SELECTOR.format(section_index + 1, subsection_index + 1)

        # Click the subsection and ensure that the page finishes reloading
        self.q(css=subsection_css).first.click()

        self._wait_for_course_section(section_title, subsection_title)

    def go_to_section_by_index(self, section_index, subsection_index):
        """
        Go to the section/subsection in the courseware.
        Every section must have at least one subsection, so specify both the
        section and subsection indices.

        Arguments:
            section_index: A 0-based index of the section to navigate to.
            subsection_index: A 0-based index of the subsection to navigate to.

        """
        try:
            section_title = self._section_titles()[section_index]
        except IndexError:
            raise ValueError("Section index '{0}' is out of range.".format(section_index))
        try:
            subsection_title = self._subsection_titles(section_index + 1)[subsection_index]
        except IndexError:
            raise ValueError("Subsection index '{0}' in section index '{1}' is out of range.".format(
                subsection_index, section_index
            ))

        self.go_to_section(section_title, subsection_title)

    def _section_title_to_index(self, section_title):
        """
        Get the section title index given the section title.
        """
        try:
            section_index = self._section_titles().index(section_title)
        except ValueError:
            raise ValueError("Could not find section '{0}'".format(section_title))

        return section_index

    def resume_course_from_outline(self):
        """
        Navigate to courseware using Resume Course button in the header.
        """
        self.q(css=self.OUTLINE_RESUME_COURSE_SELECTOR).first.click()
        courseware_page = CoursewarePage(self.browser, self.parent_page.course_id)
        courseware_page.wait_for_page()

    def _section_titles(self):
        """
        Return a list of all section titles on the page.
        """
        return self.q(css=self.SECTION_TITLES_SELECTOR).map(lambda el: el.text.strip()).results

    def _subsection_titles(self, section_index):
        """
        Return a list of all subsection titles on the page
        for the section at index `section_index` (starts at 1).
        """
        subsection_css = self.SUBSECTION_TITLES_SELECTOR.format(section_index)
        return self.q(css=subsection_css).map(
            lambda el: el.get_attribute('innerHTML').strip()
        ).results

    def _wait_for_course_section(self, section_title, subsection_title):
        """
        Ensures the user navigates to the course content page with the correct section and subsection.
        """
        courseware_page = CoursewarePage(self.browser, self.parent_page.course_id)
        courseware_page.wait_for_page()

        # TODO: TNL-6546: Remove this if/visit_unified_course_view
        if self.parent_page.unified_course_view:
            courseware_page.nav.visit_unified_course_view()

        self.wait_for(
            promise_check_func=lambda: courseware_page.nav.is_on_section(section_title, subsection_title),
            description="Waiting for course page with section '{0}' and subsection '{1}'".format(section_title, subsection_title)
        )
