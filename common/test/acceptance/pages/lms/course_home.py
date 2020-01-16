"""
LMS Course Home page object
"""


from collections import OrderedDict

from bok_choy.page_object import PageObject
from bok_choy.promise import BrokenPromise
from six import text_type

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
        self.course_outline_page = False

    def select_course_goal(self):
        """ Click on a course goal in a message """
        self.q(css='button.goal-option').first.click()
        self.wait_for_ajax()

    def is_course_goal_success_message_shown(self):
        """ Verifies course goal success message appears. """
        return self.q(css='.success-message').present

    def is_course_goal_update_field_shown(self):
        """ Verifies course goal success message appears. """
        return self.q(css='.current-goal-container').visible

    def is_course_goal_update_icon_shown(self, valid=True):
        """ Verifies course goal success or error icon appears. """
        correct_icon = 'check' if valid else 'close'
        return self.q(css='.fa-{icon}'.format(icon=correct_icon)).present

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

    def search_for_term(self, search_term):
        """
        Search within a class for a particular term.
        """
        self.q(css='.search-form > .search-input').fill(search_term)
        self.q(css='.search-form .search-button').click()
        return CourseSearchResultsPage(self.browser, self.course_id)


class CourseOutlinePage(PageObject):
    """
    Course outline fragment of page.
    """

    url = None

    def __init__(self, browser, parent_page):
        super(CourseOutlinePage, self).__init__(browser)
        self.parent_page = parent_page
        self._section_selector = '.outline-item.section'
        self._subsection_selector = '.subsection.accordion'

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
        return self._get_outline_structure_as_dictionary()

    @property
    def num_sections(self):
        """
        Return the number of sections
        """
        return len(self._get_sections_as_selenium_webelements())

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
            section_index = 0

        sections = self._get_sections_as_selenium_webelements()
        subsections = self._get_subsections(sections[section_index])
        return len(subsections)

    @property
    def num_units(self):
        """
        Return the number of units in the first subsection.

        This method returns the number of units in the horizontal navigation
        bar; not the course outline.
        """
        return len(self.q(css='.sequence-list-wrapper ol li'))

    def go_to_section(self, section_title, subsection_title):
        """
        Go to the section/subsection in the courseware.
        Every section must have at least one subsection, so specify
        both the section and subsection title.

        Example:
            go_to_section("Week 1", "Lesson 1")
        """
        subsection_webelements = self._get_subsections_as_selenium_webelements()
        subsection_titles = [self._get_outline_element_title(sub_webel)
                             for sub_webel in subsection_webelements]

        try:
            subsection_index = subsection_titles.index(text_type(subsection_title))
        except ValueError:
            raise ValueError(u"Could not find subsection '{0}' in section '{1}'".format(
                subsection_title, section_title
            ))

        target_subsection = subsection_webelements[subsection_index]
        units = self._get_units(target_subsection)

        # Click the subsection's first problem and ensure that the page finishes
        # reloading
        units[0].location_once_scrolled_into_view  # pylint: disable=W0104
        units[0].click()

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
            raise ValueError(u"Section index '{0}' is out of range.".format(section_index))
        try:
            subsection_title = self._subsection_titles(section_index)[subsection_index]
        except IndexError:
            raise ValueError(u"Subsection index '{0}' in section index '{1}' is out of range.".format(
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
            raise ValueError(u"Could not find section '{0}'".format(section_title))

        return section_index

    def resume_course_from_outline(self):
        """
        Navigate to courseware using Resume Course button in the header.
        """
        self.q(css='.btn.btn-primary.action-resume-course').results[0].click()
        courseware_page = CoursewarePage(self.browser, self.parent_page.course_id)
        courseware_page.wait_for_page()

    def _section_titles(self):
        """
        Return a list of all section titles on the page.
        """
        outline_sections = self._get_sections_as_selenium_webelements()
        section_titles = [self._get_outline_element_title(section) for section in outline_sections]
        return section_titles

    def _subsection_titles(self, section_index):
        """
        Return a list of all subsection titles on the page
        for the section at index `section_index` (starts at 0).
        """
        outline_sections = self._get_sections_as_selenium_webelements()
        target_section = outline_sections[section_index]
        target_subsections = self._get_subsections(target_section)
        subsection_titles = [self._get_outline_element_title(subsection)
                             for subsection in target_subsections]
        return subsection_titles

    def _wait_for_course_section(self, section_title, subsection_title):
        """
        Ensures the user navigates to the course content page with the correct section and
        subsection.
        """
        courseware_page = CoursewarePage(self.browser, self.parent_page.course_id)
        courseware_page.wait_for_page()

        # TODO: TNL-6546: Remove this if/visit_course_outline_page
        if self.parent_page.course_outline_page:
            courseware_page.nav.visit_course_outline_page()

        self.wait_for(
            promise_check_func=lambda: courseware_page.nav.is_on_section(
                section_title, subsection_title),
            description=u"Waiting for course page with section '{0}' and subsection '{1}'".format(
                section_title, subsection_title)
        )

    def _get_outline_structure_as_dictionary(self):
        '''
        Implements self.sections().
        '''
        outline_dict = OrderedDict()

        try:
            outline_sections = self._get_sections_as_selenium_webelements()
        except BrokenPromise:
            outline_sections = []

        for section in outline_sections:
            subsections = self._get_subsections(section)
            section_title = self._get_outline_element_title(section)
            subsection_titles = [self._get_outline_element_title(subsection)
                                 for subsection in subsections]
            outline_dict[section_title] = subsection_titles

        return outline_dict

    @staticmethod
    def _is_html_element_aria_expanded(html_element):
        return html_element.get_attribute('aria-expanded') == u'true'

    @staticmethod
    def _get_outline_element_title(outline_element):
        return outline_element.text.split('\n')[0]

    def _get_subsections(self, section):
        self._expand_all_outline_folds()
        return section.find_elements_by_css_selector(self._subsection_selector)

    def _get_units(self, subsection):
        self._expand_all_outline_folds()
        return subsection.find_elements_by_tag_name('a')

    def _get_sections_as_selenium_webelements(self):
        self._expand_all_outline_folds()
        return self.q(css=self._section_selector).results

    def _get_subsections_as_selenium_webelements(self):
        self._expand_all_outline_folds()
        return self.q(css=self._subsection_selector).results

    def get_subsection_due_date(self, index=0):
        """
        Get the due date for the given index sub-section on the LMS outline.
        """
        results = self.q(css='div.details > span.subtitle > span.subtitle-name').results
        return results[index].text if results else None

    def _expand_all_outline_folds(self):
        '''
        Expands all parts of the collapsible outline.
        '''
        expand_button_search_results = self.q(
            css='#expand-collapse-outline-all-button'
        ).results

        if not expand_button_search_results:
            return

        expand_button = expand_button_search_results[0]

        if not self._is_html_element_aria_expanded(expand_button):
            expand_button.click()


class CourseSearchResultsPage(CoursePage):
    """
    Course search page
    """

    # url = "courses/{course_id}/search/?query={query_string}"

    def is_browser_on_page(self):
        return self.q(css='.page-content > .search-results').present

    def __init__(self, browser, course_id):
        super(CourseSearchResultsPage, self).__init__(browser, course_id)
        self.course_id = course_id

    @property
    def search_results(self):
        return self.q(css='.search-results-item')
