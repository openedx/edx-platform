"""
Page classes to test either the Course Team page or the Library Team page.
"""
from bok_choy.promise import EmptyPromise
from bok_choy.page_object import PageObject
from ...tests.helpers import disable_animations
from .course_page import CoursePage
from . import BASE_URL


def wait_for_ajax_or_reload(browser):
    """
    Wait for all ajax requests to finish, OR for the page to reload.
    Normal wait_for_ajax() chokes on occasion if the pages reloads,
    giving "WebDriverException: Message: u'jQuery is not defined'"
    """
    def _is_ajax_finished():
        """ Wait for jQuery to finish all AJAX calls, if it is present. """
        return browser.execute_script("return typeof(jQuery) == 'undefined' || jQuery.active == 0")

    EmptyPromise(_is_ajax_finished, "Finished waiting for ajax requests.").fulfill()


class UsersPageMixin(PageObject):
    """ Common functionality for course/library team pages """
    new_user_form_selector = '.form-create.create-user .user-email-input'

    def url(self):
        """
        URL to this page - override in subclass
        """
        raise NotImplementedError

    def is_browser_on_page(self):
        """
        Returns True if the browser has loaded the page.
        """
        return self.q(css='body.view-team').present and not self.q(css='.ui-loading').present

    @property
    def users(self):
        """
        Return a list of users listed on this page.
        """
        return self.q(css='.user-list .user-item').map(
            lambda el: UserWrapper(self.browser, el.get_attribute('data-email'))
        ).results

    @property
    def usernames(self):
        """
        Returns a list of user names for users listed on this page
        """
        return [user.name for user in self.users]

    @property
    def has_add_button(self):
        """
        Is the "New Team Member" button present?
        """
        return self.q(css='.create-user-button').present

    def click_add_button(self):
        """
        Click on the "New Team Member" button
        """
        self.q(css='.create-user-button').first.click()
        self.wait_for(lambda: self.new_user_form_visible, "Add user form is visible")

    @property
    def new_user_form_visible(self):
        """ Is the new user form visible? """
        return self.q(css='.form-create.create-user .user-email-input').visible

    def set_new_user_email(self, email):
        """ Set the value of the "New User Email Address" field. """
        self.q(css='.form-create.create-user .user-email-input').fill(email)

    def click_submit_new_user_form(self):
        """ Submit the "New User" form """
        self.q(css='.form-create.create-user .action-primary').click()
        wait_for_ajax_or_reload(self.browser)

    def get_user(self, email):
        """ Gets user wrapper by email """
        target_users = [user for user in self.users if user.email == email]
        assert len(target_users) == 1
        return target_users[0]

    def add_user_to_course(self, email):
        """ Adds user to a course/library """
        self.wait_for_element_visibility('.create-user-button', "Add team member button is available")
        self.click_add_button()
        self.set_new_user_email(email)
        self.click_submit_new_user_form()

    def delete_user_from_course(self, email):
        """ Deletes user from course/library """
        target_user = self.get_user(email)
        target_user.click_delete()
        self.wait_for_page()

    def modal_dialog_visible(self, dialog_type):
        """ Checks if modal dialog of specified class is displayed """
        return self.q(css='.prompt.{dialog_type}'.format(dialog_type=dialog_type)).visible

    def modal_dialog_text(self, dialog_type):
        """ Gets modal dialog text """
        return self.q(css='.prompt.{dialog_type} .message'.format(dialog_type=dialog_type)).text[0]

    def wait_until_no_loading_indicator(self):
        """
        When the page first loads, there is a loading indicator and most
        functionality is not yet available. This waits for that loading to finish
        and be removed from the DOM.

        This method is different from wait_until_ready because the loading element
        is removed from the DOM, rather than hidden.

        It also disables animations for improved test reliability.
        """

        self.wait_for(
            lambda: not self.q(css='.ui-loading').present,
            "Wait for page to complete its initial loading"
        )
        disable_animations(self)

    def wait_until_ready(self):
        """
        When the page first loads, there is a loading indicator and most
        functionality is not yet available. This waits for that loading to
        finish.

        This method is different from wait_until_no_loading_indicator because this expects
        the loading indicator to still exist on the page; it is just hidden.

        It also disables animations for improved test reliability.
        """

        self.wait_for_element_invisibility(
            '.ui-loading',
            'Wait for the page to complete its initial loading'
        )
        disable_animations(self)


class LibraryUsersPage(UsersPageMixin):
    """
    Library Team page in Studio
    """
    def __init__(self, browser, locator):
        super(LibraryUsersPage, self).__init__(browser)
        self.locator = locator

    @property
    def url(self):
        """
        URL to the "User Access" page for the given library.
        """
        return "{}/library/{}/team/".format(BASE_URL, unicode(self.locator))


class CourseTeamPage(CoursePage, UsersPageMixin):
    """
    Course Team page in Studio.
    """

    url_path = "course_team"


class UserWrapper(PageObject):
    """
    A PageObject representing a wrapper around a user listed on the course/library team page.
    """
    url = None
    COMPONENT_BUTTONS = {
        'basic_tab': '.editor-tabs li.inner_tab_wrap:nth-child(1) > a',
        'advanced_tab': '.editor-tabs li.inner_tab_wrap:nth-child(2) > a',
        'save_settings': '.action-save',
    }

    def __init__(self, browser, email):
        super(UserWrapper, self).__init__(browser)
        self.email = email
        self.selector = '.user-list .user-item[data-email="{}"]'.format(self.email)

    def is_browser_on_page(self):
        """
        Sanity check that our wrapper element is on the page.
        """
        return self.q(css=self.selector).present

    def _bounded_selector(self, selector):
        """
        Return `selector`, but limited to this particular user entry's context
        """
        return '{} {}'.format(self.selector, selector)

    @property
    def name(self):
        """ Get this user's username, as displayed. """
        return self.q(css=self._bounded_selector('.user-username')).text[0]

    @property
    def role_label(self):
        """ Get this user's role, as displayed. """
        return self.q(css=self._bounded_selector('.flag-role .value')).text[0]

    @property
    def is_current_user(self):
        """ Does the UI indicate that this is the current user? """
        return self.q(css=self._bounded_selector('.flag-role .msg-you')).present

    @property
    def can_promote(self):
        """ Can this user be promoted to a more powerful role? """
        return self.q(css=self._bounded_selector('.add-admin-role')).present

    @property
    def promote_button_text(self):
        """ What does the promote user button say? """
        return self.q(css=self._bounded_selector('.add-admin-role')).text[0]

    def click_promote(self):
        """ Click on the button to promote this user to the more powerful role """
        self.q(css=self._bounded_selector('.add-admin-role')).click()
        wait_for_ajax_or_reload(self.browser)

    @property
    def can_demote(self):
        """ Can this user be demoted to a less powerful role? """
        return self.q(css=self._bounded_selector('.remove-admin-role')).present

    @property
    def demote_button_text(self):
        """ What does the demote user button say? """
        return self.q(css=self._bounded_selector('.remove-admin-role')).text[0]

    def click_demote(self):
        """ Click on the button to demote this user to the less powerful role """
        self.q(css=self._bounded_selector('.remove-admin-role')).click()
        wait_for_ajax_or_reload(self.browser)

    @property
    def can_delete(self):
        """ Can this user be deleted? """
        return self.q(css=self._bounded_selector('.action-delete:not(.is-disabled) .remove-user')).present

    def click_delete(self):
        """ Click the button to delete this user. """
        disable_animations(self)
        self.q(css=self._bounded_selector('.remove-user')).click()
        # We can't use confirm_prompt because its wait_for_ajax is flaky when the page is expected to reload.
        self.wait_for_element_visibility('.prompt', 'Prompt is visible')
        self.wait_for_element_visibility('.prompt .action-primary', 'Confirmation button is visible')
        self.q(css='.prompt .action-primary').click()
        self.wait_for_element_absence('.page-prompt .is-shown', 'Confirmation prompt is hidden')
        wait_for_ajax_or_reload(self.browser)

    @property
    def has_no_change_warning(self):
        """ Does this have a warning in place of the promote/demote buttons? """
        return self.q(css=self._bounded_selector('.notoggleforyou')).present

    @property
    def no_change_warning_text(self):
        """ Text of the warning seen in place of the promote/demote buttons. """
        return self.q(css=self._bounded_selector('.notoggleforyou')).text[0]
