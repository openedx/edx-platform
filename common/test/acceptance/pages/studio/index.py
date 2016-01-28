"""
Studio Home page
"""

from bok_choy.page_object import PageObject
from . import BASE_URL
from selenium.webdriver import ActionChains


class DashboardPage(PageObject):
    """
    Studio Home page
    """

    url = BASE_URL + "/course/"

    def is_browser_on_page(self):
        return self.q(css='body.view-dashboard').present

    @property
    def course_runs(self):
        """
        The list of course run metadata for all displayed courses
        Returns an empty string if there are none
        """
        return self.q(css='.course-run>.value').text

    @property
    def has_processing_courses(self):
        return self.q(css='.courses-processing').present

    def create_rerun(self, course_key):
        """
        Clicks the create rerun link of the course specified by course_key
        'Re-run course' link doesn't show up until you mouse over that course in the course listing
        """
        actions = ActionChains(self.browser)
        button_name = self.browser.find_element_by_css_selector('.rerun-button[href$="' + course_key + '"]')
        actions.move_to_element(button_name)
        actions.click(button_name)
        actions.perform()

    def click_course_run(self, run):
        """
        Clicks on the course with run given by run.
        """
        self.q(css='.course-run .value').filter(lambda el: el.text == run)[0].click()
        # Clicking on course with run will trigger an ajax event
        self.wait_for_ajax()

    def has_new_library_button(self):
        """
        (bool) is the "New Library" button present?
        """
        return self.q(css='.new-library-button').present

    def click_new_library(self):
        """
        Click on the "New Library" button
        """
        self.q(css='.new-library-button').first.click()
        self.wait_for_ajax()

    def is_new_library_form_visible(self):
        """
        Is the new library form visisble?
        """
        return self.q(css='.wrapper-create-library').visible

    def fill_new_library_form(self, display_name, org, number):
        """
        Fill out the form to create a new library.
        Must have called click_new_library() first.
        """
        field = lambda fn: self.q(css='.wrapper-create-library #new-library-{}'.format(fn))
        field('name').fill(display_name)
        field('org').fill(org)
        field('number').fill(number)

    def is_new_library_form_valid(self):
        """
        IS the new library form ready to submit?
        """
        return (
            self.q(css='.wrapper-create-library .new-library-save:not(.is-disabled)').present and
            not self.q(css='.wrapper-create-library .wrap-error.is-shown').present
        )

    def submit_new_library_form(self):
        """
        Submit the new library form.
        """
        self.q(css='.wrapper-create-library .new-library-save').click()

    @property
    def new_course_button(self):
        """
        Returns "New Course" button.
        """
        return self.q(css='.new-course-button')

    def is_new_course_form_visible(self):
        """
        Is the new course form visible?
        """
        return self.q(css='.wrapper-create-course').visible

    def click_new_course_button(self):
        """
        Click "New Course" button
        """
        self.q(css='.new-course-button').first.click()
        self.wait_for_ajax()

    def fill_new_course_form(self, display_name, org, number, run):
        """
        Fill out the form to create a new course.
        """
        field = lambda fn: self.q(css='.wrapper-create-course #new-course-{}'.format(fn))
        field('name').fill(display_name)
        field('org').fill(org)
        field('number').fill(number)
        field('run').fill(run)

    def is_new_course_form_valid(self):
        """
        Returns `True` if new course form is valid otherwise `False`.
        """
        return (
            self.q(css='.wrapper-create-course .new-course-save:not(.is-disabled)').present and
            not self.q(css='.wrapper-create-course .wrap-error.is-shown').present
        )

    def submit_new_course_form(self):
        """
        Submit the new course form.
        """
        self.q(css='.wrapper-create-course .new-course-save').first.click()
        self.wait_for_ajax()

    @property
    def error_notification(self):
        """
        Returns error notification element.
        """
        return self.q(css='.wrapper-notification-error.is-shown')

    @property
    def error_notification_message(self):
        """
        Returns text of error message.
        """
        self.wait_for_element_visibility(
            ".wrapper-notification-error.is-shown .message", "Error message is visible"
        )
        return self.error_notification.results[0].find_element_by_css_selector('.message').text

    @property
    def course_org_field(self):
        """
        Returns course organization input.
        """
        return self.q(css='.wrapper-create-course #new-course-org')

    def select_item_in_autocomplete_widget(self, item_text):
        """
        Selects item in autocomplete where text of item matches item_text.
        """
        self.wait_for_element_visibility(
            ".ui-autocomplete .ui-menu-item", "Autocomplete widget is visible"
        )
        self.q(css='.ui-autocomplete .ui-menu-item a').filter(lambda el: el.text == item_text)[0].click()

    def list_courses(self):
        """
        List all the courses found on the page's list of libraries.
        """
        # Workaround Selenium/Firefox bug: `.text` property is broken on invisible elements
        course_tab_link = self.q(css='#course-index-tabs .courses-tab a')
        if course_tab_link:
            course_tab_link.click()
        div2info = lambda element: {
            'name': element.find_element_by_css_selector('.course-title').text,
            'org': element.find_element_by_css_selector('.course-org .value').text,
            'number': element.find_element_by_css_selector('.course-num .value').text,
            'run': element.find_element_by_css_selector('.course-run .value').text,
            'url': element.find_element_by_css_selector('a.course-link').get_attribute('href'),
        }
        return self.q(css='.courses li.course-item').map(div2info).results

    def has_course(self, org, number, run):
        """
        Returns `True` if course for given org, number and run exists on the page otherwise `False`
        """
        for course in self.list_courses():
            if course['org'] == org and course['number'] == number and course['run'] == run:
                return True
        return False

    def list_libraries(self):
        """
        Click the tab to display the available libraries, and return detail of them.
        """
        # Workaround Selenium/Firefox bug: `.text` property is broken on invisible elements
        self.q(css='#course-index-tabs .libraries-tab a').click()
        if self.q(css='.list-notices.libraries-tab').present:
            # No libraries are available.
            self.wait_for_element_visibility('.libraries-tab .new-library-button', "Switch to library tab")
            return []
        div2info = lambda element: {
            'name': element.find_element_by_css_selector('.course-title').text,
            'org': element.find_element_by_css_selector('.course-org .value').text,
            'number': element.find_element_by_css_selector('.course-num .value').text,
            'url': element.find_element_by_css_selector('a.library-link').get_attribute('href'),
        }
        self.wait_for_element_visibility('.libraries li.course-item', "Switch to library tab")
        return self.q(css='.libraries li.course-item').map(div2info).results

    def has_library(self, **kwargs):
        """
        Does the page's list of libraries include a library matching kwargs?
        """
        for lib in self.list_libraries():
            if all([lib[key] == kwargs[key] for key in kwargs]):
                return True
        return False


class DashboardPageWithPrograms(DashboardPage):
    """
    Extends DashboardPage for bok choy testing programs-related behavior.
    """

    def is_programs_tab_present(self):
        """
        Determine if the programs tab appears on the studio home page.
        """
        return self.q(css='#course-index-tabs .programs-tab a').present

    def _click_programs_tab(self):
        """
        DRY helper.
        """
        self.q(css='#course-index-tabs .programs-tab a').click()
        self.wait_for_element_visibility("div.programs-tab.active", "Switch to programs tab")

    def is_new_program_button_present(self):
        """
        Determine if the "new program" button is visible in the top "nav
        actions" section of the page.
        """
        return self.q(css='.nav-actions a.new-program-button').present

    def is_empty_list_create_button_present(self):
        """
        Determine if the "create your first program" button is visible under
        the programs tab (when the program list result is empty).
        """
        self._click_programs_tab()
        return self.q(css='div.programs-tab.active a.new-program-button').present

    def get_program_list(self):
        """
        Fetch the content of the program list under the programs tab (assuming
        it is nonempty).
        """
        self._click_programs_tab()
        div2info = lambda element: (
            element.find_element_by_css_selector('.course-title').text,  # name
            element.find_element_by_css_selector('.course-org .value').text,  # org key
        )
        return self.q(css='div.programs-tab li.course-item').map(div2info).results
