"""
Studio Index, home and dashboard pages. These are the starting pages for users.
"""
from bok_choy.page_object import PageObject
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys

from common.test.acceptance.pages.studio import BASE_URL
from common.test.acceptance.pages.studio.login import LoginPage
from common.test.acceptance.pages.studio.signup import SignupPage
from common.test.acceptance.pages.studio.utils import HelpMixin


class HeaderMixin(object):
    """
    Mixin class used for the pressing buttons in the header.
    """
    def click_sign_up(self):
        """
        Press the Sign Up button in the header.
        """
        next_page = SignupPage(self.browser)
        self.q(css='.action-signup')[0].click()
        return next_page.wait_for_page()

    def click_sign_in(self):
        """
        Press the Sign In button in the header.
        """
        next_page = LoginPage(self.browser)
        self.q(css='.action-signin')[0].click()
        return next_page.wait_for_page()


class IndexPage(PageObject, HeaderMixin, HelpMixin):
    """
    Home page for Studio when not logged in.
    """
    url = BASE_URL + "/"

    def is_browser_on_page(self):
        return self.q(css='.wrapper-text-welcome').visible


class DashboardPage(PageObject, HelpMixin):
    """
    Studio Dashboard page with courses.
    The user must be logged in to access this page.
    """
    url = BASE_URL + "/course/"

    def is_browser_on_page(self):
        return self.q(css='.content-primary').visible

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

    def scroll_to_course(self, course_key):
        """
        Scroll down to the course element
        """
        element = '[data-course-key*="{}"]'.format(course_key)
        self.scroll_to_element(element)

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
        Is the new library form ready to submit?
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

    def list_courses(self, archived=False):
        """
        List all the courses found on the page's list of courses.
        """
        # Workaround Selenium/Firefox bug: `.text` property is broken on invisible elements
        tab_selector = '#course-index-tabs .{} a'.format('archived-courses-tab' if archived else 'courses-tab')
        self.wait_for_element_presence(tab_selector, "Courses Tab")
        self.q(css=tab_selector).click()
        div2info = lambda element: {
            'name': element.find_element_by_css_selector('.course-title').text,
            'org': element.find_element_by_css_selector('.course-org .value').text,
            'number': element.find_element_by_css_selector('.course-num .value').text,
            'run': element.find_element_by_css_selector('.course-run .value').text,
            'url': element.find_element_by_css_selector('a.course-link').get_attribute('href'),
        }
        course_list_selector = '.{} li.course-item'.format('archived-courses' if archived else 'courses')
        return self.q(css=course_list_selector).map(div2info).results

    def has_course(self, org, number, run, archived=False):
        """
        Returns `True` if course for given org, number and run exists on the page otherwise `False`
        """
        for course in self.list_courses(archived):
            if course['org'] == org and course['number'] == number and course['run'] == run:
                return True
        return False

    def list_libraries(self):
        """
        Click the tab to display the available libraries, and return detail of them.
        """
        # Workaround Selenium/Firefox bug: `.text` property is broken on invisible elements
        library_tab_css = '#course-index-tabs .libraries-tab'
        self.wait_for_element_presence(library_tab_css, "Libraries tab")
        self.q(css=library_tab_css).click()
        if self.q(css='.list-notices.libraries-tab').present:
            # No libraries are available.
            self.wait_for_element_presence('.libraries-tab .new-library-button', "new library tab")
            return []
        div2info = lambda element: {
            'name': element.find_element_by_css_selector('.course-title').text,
            'link_element': element.find_element_by_css_selector('.course-title'),
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

    def click_library(self, name):
        """
        Click on the library with the given name.
        """
        for lib in self.list_libraries():
            if lib['name'] == name:
                lib['link_element'].click()

    @property
    def language_selector(self):
        """
        return language selector
        """
        self.wait_for_element_visibility(
            '#settings-language-value',
            'Language selector element is available'
        )
        return self.q(css='#settings-language-value')

    @property
    def course_creation_error_message(self):
        """
        Returns the course creation error
        """
        self.wait_for_element_visibility(
            '#course_creation_error>p',
            'Length error is present'
        )
        return self.q(css='#course_creation_error>p').text[0]

    def is_create_button_disabled(self):
        """
        Returns: True if Create button is disbaled
        """
        self.wait_for_element_presence(
            '.action.action-primary.new-course-save.is-disabled',
            "Create button is disabled"
        )
        return True


class HomePage(DashboardPage):
    """
    Home page for Studio when logged in.
    """
    url = BASE_URL + "/home/"


class AccessibilityPage(IndexPage):
    """
    Home page for Studio when logged in.
    """
    url = BASE_URL + "/accessibility"

    def is_browser_on_page(self):
        """
        Is the page header visible?
        """
        return self.q(css='#root h2').visible

    def header_text_on_page(self):
        """
        Check that the page header has the right text.
        """
        return 'Individualized Accessibility Process for Course Creators' in self.q(css='#root h2').text

    def fill_form(self, email, name, message):
        """
        Fill the accessibility feedback form out.
        """
        email_input = self.q(css='#root input#email')
        name_input = self.q(css='#root input#fullName')
        message_input = self.q(css='#root textarea#message')

        email_input.fill(email)
        name_input.fill(name)
        message_input.fill(message)

        # Tab off the message textarea to trigger any error messages
        message_input[0].send_keys(Keys.TAB)

    def submit_form(self):
        """
        Click the submit button on the accessibiltiy feedback form.
        """
        button = self.q(css='#root section button')[0]
        button.click()
        self.wait_for_element_visibility('#root div.alert-dialog', 'Form submission alert is visible')

    def leave_field_blank(self, field_id, field_type='input'):
        """
        To simulate leaving a field blank, click on the field, then press TAB to move off focus off the field.
        """
        field = self.q(css='#root {}#{}'.format(field_type, field_id))[0]
        field.click()
        field.send_keys(Keys.TAB)

    def alert_has_text(self, text=''):
        """
        Check that the alert dialog contains the specified text.
        """
        return text in self.q(css='#root div.alert-dialog').text

    def error_message_is_shown_with_text(self, field_id, text=''):
        """
        Check that at least one error message is shown and at least one contains the specified text.
        """
        selector = '#root div#error-{}'.format(field_id)
        self.wait_for_element_visibility(selector, 'An error message is visible')
        error_messages = self.q(css=selector)
        for message in error_messages:
            if text in message.text:
                return True
        return False
