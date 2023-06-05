"""
Courseware page.
"""


from bok_choy.promise import EmptyPromise

from common.test.acceptance.pages.lms.course_page import CoursePage


class CoursewarePage(CoursePage):
    """
    Course info.
    """

    url_path = "courseware/"
    xblock_component_selector = '.vert .xblock'

    # TODO: TNL-6546: Remove sidebar selectors
    section_selector = '.chapter'
    subsection_selector = '.chapter-content-container a'

    def __init__(self, browser, course_id):
        super(CoursewarePage, self).__init__(browser, course_id)
        # self.nav = CourseNavPage(browser, self)

    def is_browser_on_page(self):
        return self.q(css='.course-content').present

    def go_to_sequential_position(self, sequential_position):
        """
        Within a section/subsection navigate to the sequential position specified by `sequential_position`.

        Arguments:
            sequential_position (int): position in sequential bar
        """
        def is_at_new_position():
            """
            Returns whether the specified tab has become active. It is defensive
            against the case where the page is still being loaded.
            """
            active_tab = self._active_sequence_tab
            try:
                return active_tab and int(active_tab.attrs('data-element')[0]) == sequential_position
            except IndexError:
                return False

        sequential_position_css = u'#sequence-list #tab_{0}'.format(sequential_position - 1)
        self.q(css=sequential_position_css).first.click()
        EmptyPromise(is_at_new_position, "Position navigation fulfilled").fulfill()

    @property
    def _active_sequence_tab(self):
        return self.q(css='#sequence-list .nav-item.active')

    def click_next_button_on_top(self):
        self._click_navigation_button('sequence-nav', 'button-next')

    def _click_navigation_button(self, top_or_bottom_class, next_or_previous_class):
        """
        Clicks the navigation button, given the respective CSS classes.
        """
        previous_tab_id = self._active_sequence_tab.attrs('data-id')[0]

        def is_at_new_tab_id():
            """
            Returns whether the active tab has changed. It is defensive
            against the case where the page is still being loaded.
            """
            active_tab = self._active_sequence_tab
            try:
                return active_tab and previous_tab_id != active_tab.attrs('data-id')[0]
            except IndexError:
                return False

        self.q(
            css=u'.{} > .sequence-nav-button.{}'.format(top_or_bottom_class, next_or_previous_class)
        ).first.click()
        EmptyPromise(is_at_new_tab_id, "Button navigation fulfilled").fulfill()
