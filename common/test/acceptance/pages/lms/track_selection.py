"""Track selection page"""

from urllib import urlencode

from bok_choy.page_object import PageObject, unguarded
from bok_choy.promise import Promise, EmptyPromise
from . import BASE_URL
from .dashboard import DashboardPage
from .pay_and_verify import PaymentAndVerificationFlow


class TrackSelectionPage(PageObject):
    """Interact with the track selection page.

    This page can be accessed at `/course_modes/choose/{course_id}/`.
    """
    def __init__(self, browser, course_id, separate_verified=False):
        """Initialize the page.

        Arguments:
            browser (Browser): The browser instance.
            course_id (unicode): The course in which the user is enrolling.

        Keyword Arguments:
            separate_verified (Boolean): Whether to use the split payment and
                verification flow when enrolling as verified.
        """
        super(TrackSelectionPage, self).__init__(browser)
        self._course_id = course_id
        self._separate_verified = separate_verified

        if self._separate_verified:
            self._querystring = "?separate-verified=1"
        else:
            self._querystring = "?disable-separate-verified=1"

    @property
    def url(self):
        """Return the URL corresponding to the track selection page."""
        url = "{base}/course_modes/choose/{course_id}/{querystring}".format(
            base=BASE_URL,
            course_id=self._course_id,
            querystring=self._querystring
        )

        return url

    def is_browser_on_page(self):
        """Check if the track selection page has loaded."""
        return self.q(css=".wrapper-register-choose").is_present()

    def enroll(self, mode="honor"):
        """Interact with one of the enrollment buttons on the page.

            Keyword Arguments:
                mode (str): Can be "honor" or "verified"

            Raises:
                ValueError
        """
        if mode == "honor":
            self.q(css="input[name='honor_mode']").click()

            return DashboardPage(self.browser, separate_verified=self._separate_verified).wait_for_page()
        elif mode == "verified":
            # Check the first contribution option, then click the enroll button
            self.q(css=".contribution-option > input").first.click()
            self.q(css="input[name='verified_mode']").click()

            return PaymentAndVerificationFlow(self.browser, self._course_id).wait_for_page()
        else:
            raise ValueError("Mode must be either 'honor' or 'verified'.")
