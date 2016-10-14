"""
Courseware page.
"""

from common.test.acceptance.pages.lms.course_page import CoursePage
from bok_choy.promise import EmptyPromise
from selenium.webdriver.common.action_chains import ActionChains


class CoursewarePage(CoursePage):
    """
    Course info.
    """

    url_path = "courseware/"
    xblock_component_selector = '.vert .xblock'
    section_selector = '.chapter'
    subsection_selector = '.chapter-content-container a'

    def is_browser_on_page(self):
        return self.q(css='body.courseware').present

    @property
    def chapter_count_in_navigation(self):
        """
        Returns count of chapters available on LHS navigation.
        """
        return len(self.q(css='nav.course-navigation a.chapter'))

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

    def verify_tooltips_displayed(self):
        """
        Verify that all sequence navigation bar tooltips are being displayed upon mouse hover.

        If a tooltip does not appear, raise a BrokenPromise.
        """
        for index, tab in enumerate(self.q(css='#sequence-list > li')):
            ActionChains(self.browser).move_to_element(tab).perform()
            self.wait_for_element_visibility(
                '#tab_{index} > .sequence-tooltip'.format(index=index),
                'Tab {index} should appear'.format(index=index)
            )

    @property
    def course_license(self):
        """
        Returns the course license text, if present. Else returns None.
        """
        element = self.q(css="#content .container-footer .course-license")
        if element.is_present():
            return element.text[0]
        return None

    def go_to_sequential_position(self, sequential_position):
        """
        Within a section/subsection navigate to the sequential position specified by `sequential_position`.

        Arguments:
            sequential_position (int): position in sequential bar
        """
        sequential_position_css = '#sequence-list #tab_{0}'.format(sequential_position - 1)
        self.q(css=sequential_position_css).first.click()

    @property
    def sequential_position(self):
        """
        Returns the position of the active tab in the sequence.
        """
        tab_id = self._active_sequence_tab.attrs('id')[0]
        return int(tab_id.split('_')[1])

    @property
    def _active_sequence_tab(self):  # pylint: disable=missing-docstring
        return self.q(css='#sequence-list .nav-item.active')

    @property
    def is_next_button_enabled(self):  # pylint: disable=missing-docstring
        return not self.q(css='.sequence-nav > .sequence-nav-button.button-next.disabled').is_present()

    @property
    def is_previous_button_enabled(self):  # pylint: disable=missing-docstring
        return not self.q(css='.sequence-nav > .sequence-nav-button.button-previous.disabled').is_present()

    def click_next_button_on_top(self):  # pylint: disable=missing-docstring
        self._click_navigation_button('sequence-nav', 'button-next')

    def click_next_button_on_bottom(self):  # pylint: disable=missing-docstring
        self._click_navigation_button('sequence-bottom', 'button-next')

    def click_previous_button_on_top(self):  # pylint: disable=missing-docstring
        self._click_navigation_button('sequence-nav', 'button-previous')

    def click_previous_button_on_bottom(self):  # pylint: disable=missing-docstring
        self._click_navigation_button('sequence-bottom', 'button-previous')

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
            return active_tab and previous_tab_id != active_tab.attrs('data-id')[0]

        button_css = '.{} > .sequence-nav-button.{}'.format(top_or_bottom_class, next_or_previous_class)
        self.wait_for_element_presence(button_css, "Navigation button present")
        self.q(
            css=button_css
        ).first.click()
        EmptyPromise(is_at_new_tab_id, "Button navigation fulfilled").fulfill()

    @property
    def can_start_proctored_exam(self):
        """
        Returns True if the timed/proctored exam timer bar is visible on the courseware.
        """
        return self.q(css='button.start-timed-exam[data-start-immediately="false"]').is_present()

    def start_timed_exam(self):
        """
        clicks the start this timed exam link
        """
        self.q(css=".xblock-student_view .timed-exam .start-timed-exam").first.click()
        self.wait_for_element_presence(".proctored_exam_status .exam-timer", "Timer bar")

    def stop_timed_exam(self):
        """
        clicks the stop this timed exam link
        """
        self.q(css=".proctored_exam_status button.exam-button-turn-in-exam").first.click()
        self.wait_for_element_absence(".proctored_exam_status .exam-button-turn-in-exam", "End Exam Button gone")
        self.wait_for_element_presence("button[name='submit-proctored-exam']", "Submit Exam Button")
        self.q(css="button[name='submit-proctored-exam']").first.click()
        self.wait_for_element_absence(".proctored_exam_status .exam-timer", "Timer bar")

    def start_proctored_exam(self):
        """
        clicks the start this timed exam link
        """
        self.q(css='button.start-timed-exam[data-start-immediately="false"]').first.click()

        # Wait for the unique exam code to appear.
        # self.wait_for_element_presence(".proctored-exam-code", "unique exam code")

    def has_submitted_exam_message(self):
        """
        Returns whether the "you have submitted your exam" message is present.
        This being true implies "the exam contents and results are hidden".
        """
        return self.q(css="div.proctored-exam.completed").visible

    def content_hidden_past_due_date(self, content_type="subsection"):
        """
        Returns whether the "the due date for this ___ has passed" message is present.
        ___ is the type of the hidden content, and defaults to subsection.
        This being true implies "the ___ contents are hidden because their due date has passed".
        """
        message = "The due date for this {0} has passed.".format(content_type)
        if self.q(css="div.seq_content").is_present():
            return False
        for html in self.q(css="div.hidden-content").html:
            if message in html:
                return True
        return False

    @property
    def entrance_exam_message_selector(self):
        """
        Return the entrance exam status message selector on the top of courseware page.
        """
        return self.q(css='#content .container section.course-content .sequential-status-message')

    def has_entrance_exam_message(self):
        """
        Returns boolean indicating presence entrance exam status message container div.
        """
        return self.entrance_exam_message_selector.is_present()

    def has_passed_message(self):
        """
        Returns boolean indicating presence of passed message.
        """
        return self.entrance_exam_message_selector.is_present() \
            and "You have passed the entrance exam" in self.entrance_exam_message_selector.text[0]

    def has_banner(self):
        """
        Returns boolean indicating presence of banner
        """
        return self.q(css='.pattern-library-shim').is_present()

    @property
    def is_timer_bar_present(self):
        """
        Returns True if the timed/proctored exam timer bar is visible on the courseware.
        """
        return self.q(css=".proctored_exam_status .exam-timer").is_present()

    def active_usage_id(self):
        """ Returns the usage id of active sequence item """
        get_active = lambda el: 'active' in el.get_attribute('class')
        attribute_value = lambda el: el.get_attribute('data-id')
        return self.q(css='#sequence-list .nav-item').filter(get_active).map(attribute_value).results[0]

    @property
    def breadcrumb(self):
        """ Return the course tree breadcrumb shown above the sequential bar """
        return [part.strip() for part in self.q(css='.path').text[0].split('>')]

    def unit_title_visible(self):
        """ Check if unit title is visible """
        return self.q(css='.unit-title').visible

    def bookmark_button_visible(self):
        """ Check if bookmark button is visible """
        EmptyPromise(lambda: self.q(css='.bookmark-button').visible, "Bookmark button visible").fulfill()
        return True

    @property
    def bookmark_button_state(self):
        """ Return `bookmarked` if button is in bookmarked state else '' """
        return 'bookmarked' if self.q(css='.bookmark-button.bookmarked').present else ''

    @property
    def bookmark_icon_visible(self):
        """ Check if bookmark icon is visible on active sequence nav item """
        return self.q(css='.active .bookmark-icon').visible

    def click_bookmark_unit_button(self):
        """ Bookmark a unit by clicking on Bookmark button """
        previous_state = self.bookmark_button_state
        self.q(css='.bookmark-button').first.click()
        EmptyPromise(lambda: self.bookmark_button_state != previous_state, "Bookmark button toggled").fulfill()


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
