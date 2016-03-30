"""Login and Registration pages """

from urllib import urlencode
from bok_choy.page_object import PageObject, unguarded
from bok_choy.promise import Promise, EmptyPromise
from . import BASE_URL
from .dashboard import DashboardPage


class RegisterPage(PageObject):
    """
    Registration page (create a new account)
    """

    def __init__(self, browser, course_id):
        """
        Course ID is currently of the form "edx/999/2013_Spring"
        but this format could change.
        """
        super(RegisterPage, self).__init__(browser)
        self._course_id = course_id

    @property
    def url(self):
        """
        URL for the registration page of a course.
        """
        return "{base}/register?course_id={course_id}&enrollment_action={action}".format(
            base=BASE_URL,
            course_id=self._course_id,
            action="enroll",
        )

    def is_browser_on_page(self):
        return any([
            'register' in title.lower()
            for title in self.q(css='span.title-sub').text
        ])

    def provide_info(self, email, password, username, full_name):
        """
        Fill in registration info.
        `email`, `password`, `username`, and `full_name` are the user's credentials.
        """
        self.wait_for_element_visibility('input#email', 'Email field is shown')
        self.q(css='input#email').fill(email)
        self.q(css='input#password').fill(password)
        self.q(css='input#username').fill(username)
        self.q(css='input#name').fill(full_name)
        self.q(css='input#tos-yes').first.click()
        self.q(css='input#honorcode-yes').first.click()
        self.q(css="#country option[value='US']").first.click()

    def submit(self):
        """
        Submit registration info to create an account.
        """
        self.q(css='button#submit').first.click()

        # The next page is the dashboard; make sure it loads
        dashboard = DashboardPage(self.browser)
        dashboard.wait_for_page()
        return dashboard


class ResetPasswordPage(PageObject):
    """Initialize the page.

        Arguments:
            browser (Browser): The browser instance.
    """
    url = BASE_URL + "/login#forgot-password-modal"

    def __init__(self, browser):
        super(ResetPasswordPage, self).__init__(browser)

    def is_browser_on_page(self):
        return (
            self.q(css="#login-anchor").is_present() and
            self.q(css="#password-reset-anchor").is_present()
        )

    def is_form_visible(self):
        return (
            not self.q(css="#login-anchor").visible and
            self.q(css="#password-reset-form").visible
        )

    def fill_password_reset_form(self, email):
        """
        Fill in the form and submit it
        """
        self.wait_for_element_visibility('#password-reset-email', 'Reset Email field is shown')
        self.q(css="#password-reset-email").fill(email)
        self.q(css="button.js-reset").click()

    def is_success_visible(self, selector):
        """
        Check element is visible
        """
        self.wait_for_element_visibility(selector, 'Success div is shown')

    def get_success_message(self):
        """
        Return a success message displayed to the user
        """
        return self.q(css=".submission-success h4").text


class CombinedLoginAndRegisterPage(PageObject):
    """Interact with combined login and registration page.

    This page is currently hidden behind the feature flag
    `ENABLE_COMBINED_LOGIN_REGISTRATION`, which is enabled
    in the bok choy settings.

    When enabled, the new page is available from either
    `/login` or `/register`; the new page is also served at
    `/account/login/` or `/account/register/`, where it was
    available for a time during an A/B test.

    Users can reach this page while attempting to enroll
    in a course, in which case users will be auto-enrolled
    when they successfully authenticate (unless the course
    has been paywalled).

    """
    def __init__(self, browser, start_page="register", course_id=None):
        """Initialize the page.

        Arguments:
            browser (Browser): The browser instance.

        Keyword Args:
            start_page (str): Whether to start on the login or register page.
            course_id (unicode): If provided, load the page as if the user
                is trying to enroll in a course.

        """
        super(CombinedLoginAndRegisterPage, self).__init__(browser)
        self._course_id = course_id

        if start_page not in ["register", "login"]:
            raise ValueError("Start page must be either 'register' or 'login'")
        self._start_page = start_page

    @property
    def url(self):
        """Return the URL for the combined login/registration page. """
        url = "{base}/{login_or_register}".format(
            base=BASE_URL,
            login_or_register=self._start_page
        )

        # These are the parameters that would be included if the user
        # were trying to enroll in a course.
        if self._course_id is not None:
            url += "?{params}".format(
                params=urlencode({
                    "course_id": self._course_id,
                    "enrollment_action": "enroll"
                })
            )

        return url

    def is_browser_on_page(self):
        """Check whether the combined login/registration page has loaded. """
        return (
            self.q(css="#login-anchor").is_present() and
            self.q(css="#register-anchor").is_present() and
            self.current_form is not None
        )

    def toggle_form(self):
        """Toggle between the login and registration forms. """
        old_form = self.current_form

        # Toggle the form
        if old_form == "login":
            self.q(css=".form-toggle[data-type='register']").click()
        else:
            self.q(css=".form-toggle[data-type='login']").click()

        # Wait for the form to change before returning
        EmptyPromise(
            lambda: self.current_form != old_form,
            "Finish toggling to the other form"
        ).fulfill()

    def register(
            self, email="", password="", username="", full_name="", country="", favorite_movie="",
            terms_of_service=False
    ):
        """Fills in and submits the registration form.

        Requires that the "register" form is visible.
        This does NOT wait for the next page to load,
        so the caller should wait for the next page
        (or errors if that's the expected behavior.)

        Keyword Arguments:
            email (unicode): The user's email address.
            password (unicode): The user's password.
            username (unicode): The user's username.
            full_name (unicode): The user's full name.
            country (unicode): Two-character country code.
            terms_of_service (boolean): If True, agree to the terms of service and honor code.

        """
        # Fill in the form
        self.wait_for_element_visibility('#register-email', 'Email field is shown')
        if email:
            self.q(css="#register-email").fill(email)
        if full_name:
            self.q(css="#register-name").fill(full_name)
        if username:
            self.q(css="#register-username").fill(username)
        if password:
            self.q(css="#register-password").fill(password)
        if country:
            self.q(css="#register-country option[value='{country}']".format(country=country)).click()
        if favorite_movie:
            self.q(css="#register-favorite_movie").fill(favorite_movie)
        if terms_of_service:
            self.q(css="#register-honor_code").click()

        # Submit it
        self.q(css=".register-button").click()

    def login(self, email="", password=""):
        """Fills in and submits the login form.

        Requires that the "login" form is visible.
        This does NOT wait for the next page to load,
        so the caller should wait for the next page
        (or errors if that's the expected behavior).

        Keyword Arguments:
            email (unicode): The user's email address.
            password (unicode): The user's password.

        """
        # Fill in the form
        self.wait_for_element_visibility('#login-email', 'Email field is shown')
        self.q(css="#login-email").fill(email)
        self.q(css="#login-password").fill(password)

        # Submit it
        self.q(css=".login-button").click()

    def click_third_party_dummy_provider(self):
        """Clicks on the Dummy third party provider login button.

        Requires that the "login" form is visible.
        This does NOT wait for the ensuing page[s] to load.
        Only the "Dummy" provider is used for bok choy because it is the only
        one that doesn't send traffic to external servers.
        """
        self.q(css="button.{}-oa2-dummy".format(self.current_form)).click()

    def password_reset(self, email):
        """Navigates to, fills in, and submits the password reset form.

        Requires that the "login" form is visible.

        Keyword Arguments:
            email (unicode): The user's email address.

        """
        login_form = self.current_form

        # Click the password reset link on the login page
        self.q(css="a.forgot-password").click()

        # Wait for the password reset form to load
        EmptyPromise(
            lambda: self.current_form != login_form,
            "Finish toggling to the password reset form"
        ).fulfill()

        # Fill in the form
        self.wait_for_element_visibility('#password-reset-email', 'Email field is shown')
        self.q(css="#password-reset-email").fill(email)

        # Submit it
        self.q(css="button.js-reset").click()

        return CombinedLoginAndRegisterPage(self.browser).wait_for_page()

    @property
    @unguarded
    def current_form(self):
        """Return the form that is currently visible to the user.

        Returns:
            Either "register", "login", or "password-reset" if a valid
            form is loaded.

            If we can't find any of these forms on the page, return None.

        """
        if self.q(css=".register-button").visible:
            return "register"
        elif self.q(css=".login-button").visible:
            return "login"
        elif self.q(css=".js-reset").visible:
            return "password-reset"
        elif self.q(css=".proceed-button").visible:
            return "hinted-login"

    @property
    def email_value(self):
        """ Current value of the email form field """
        return self.q(css="#register-email").attrs('value')[0]

    @property
    def full_name_value(self):
        """ Current value of the full_name form field """
        return self.q(css="#register-name").attrs('value')[0]

    @property
    def username_value(self):
        """ Current value of the username form field """
        return self.q(css="#register-username").attrs('value')[0]

    @property
    def errors(self):
        """Return a list of errors displayed to the user. """
        return self.q(css=".submission-error li").text

    def wait_for_errors(self):
        """Wait for errors to be visible, then return them. """
        def _check_func():
            """Return success status and any errors that occurred."""
            errors = self.errors
            return (bool(errors), errors)
        return Promise(_check_func, "Errors are visible").fulfill()

    @property
    def success(self):
        """Return a success message displayed to the user."""
        if self.q(css=".submission-success").visible:
            return self.q(css=".submission-success h4").text

    def wait_for_success(self):
        """Wait for a success message to be visible, then return it."""
        def _check_func():
            """Return success status and any errors that occurred."""
            success = self.success
            return (bool(success), success)
        return Promise(_check_func, "Success message is visible").fulfill()

    @unguarded  # Because we go from this page -> temporary page -> this page again when testing the Dummy provider
    def wait_for_auth_status_message(self):
        """Wait for a status message to be visible following third_party registration, then return it."""
        def _check_func():
            """Return third party auth status notice message."""
            for selector in ['.already-authenticated-msg p', '.status p']:
                msg_element = self.q(css=selector)
                if msg_element.visible:
                    return (True, msg_element.text[0])
            return (False, None)
        return Promise(_check_func, "Result of third party auth is visible").fulfill()

    @property
    def hinted_login_prompt(self):
        """Get the message displayed to the user on the hinted-login form"""
        if self.q(css=".wrapper-other-login .instructions").visible:
            return self.q(css=".wrapper-other-login .instructions").text[0]
