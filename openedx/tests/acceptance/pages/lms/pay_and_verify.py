"""Payment and verification pages"""

import re

from bok_choy.page_object import PageObject
from bok_choy.promise import Promise
from openedx.tests.acceptance.pages.lms import BASE_URL
from openedx.tests.acceptance.pages.lms.dashboard import DashboardPage


class PaymentAndVerificationFlow(PageObject):
    """Interact with the split payment and verification flow.

    The flow can be accessed at the following URLs:
        `/verify_student/start-flow/{course}/`
        `/verify_student/upgrade/{course}/`
        `/verify_student/verify-now/{course}/`
        `/verify_student/verify-later/{course}/`
        `/verify_student/payment-confirmation/{course}/`

    Users can reach the flow when attempting to enroll in a course's verified
    mode, either directly from the track selection page, or by upgrading from
    the honor mode. Users can also reach the flow when attempting to complete
    a deferred verification, or when attempting to view a receipt corresponding
    to an earlier payment.
    """
    def __init__(self, browser, course_id, entry_point='start-flow'):
        """Initialize the page.

        Arguments:
            browser (Browser): The browser instance.
            course_id (unicode): The course in which the user is enrolling.

        Keyword Arguments:
            entry_point (str): Where to begin the flow; must be one of 'start-flow',
                'upgrade', 'verify-now', verify-later', or 'payment-confirmation'.

        Raises:
            ValueError
        """
        super(PaymentAndVerificationFlow, self).__init__(browser)
        self._course_id = course_id

        if entry_point not in ['start-flow', 'upgrade', 'verify-now', 'verify-later', 'payment-confirmation']:
            raise ValueError(
                "Entry point must be either 'start-flow', 'upgrade', 'verify-now', 'verify-later', or 'payment-confirmation'."
            )
        self._entry_point = entry_point

    @property
    def url(self):
        """Return the URL corresponding to the initial position in the flow."""
        url = "{base}/verify_student/{entry_point}/{course}/".format(
            base=BASE_URL,
            entry_point=self._entry_point,
            course=self._course_id
        )

        return url

    def is_browser_on_page(self):
        """Check if a step in the payment and verification flow has loaded."""
        return (
            self.q(css="div .make-payment-step").is_present() or
            self.q(css="div .payment-confirmation-step").is_present() or
            self.q(css="div .face-photo-step").is_present() or
            self.q(css="div .id-photo-step").is_present() or
            self.q(css="div .review-photos-step").is_present() or
            self.q(css="div .enrollment-confirmation-step").is_present()
        )

    def indicate_contribution(self):
        """Interact with the radio buttons appearing on the first page of the upgrade flow."""
        self.q(css=".contribution-option > input").first.click()

    def proceed_to_payment(self):
        """Interact with the payment button."""
        self.q(css=".payment-button").click()

        FakePaymentPage(self.browser, self._course_id).wait_for_page()

    def immediate_verification(self):
        """Interact with the immediate verification button."""
        self.q(css="#verify_now_button").click()

        PaymentAndVerificationFlow(self.browser, self._course_id, entry_point='verify-now').wait_for_page()

    def defer_verification(self):
        """Interact with the link allowing the user to defer their verification."""
        self.q(css="#verify_later_button").click()

        DashboardPage(self.browser).wait_for_page()

    def webcam_capture(self):
        """Interact with a webcam capture button."""
        self.q(css="#webcam_capture_button").click()

        def _check_func():
            next_step_button_classes = self.q(css="#next_step_button").attrs('class')
            next_step_button_enabled = 'is-disabled' not in next_step_button_classes
            return (next_step_button_enabled, next_step_button_classes)

        # Check that the #next_step_button is enabled before returning control to the caller
        Promise(_check_func, "The 'Next Step' button is enabled.").fulfill()

    def next_verification_step(self, next_page_object):
        """Interact with the 'Next' step button found in the verification flow."""
        self.q(css="#next_step_button").click()

        next_page_object.wait_for_page()

    def go_to_dashboard(self):
        """Interact with the link to the dashboard appearing on the enrollment confirmation page."""
        if self.q(css="div .enrollment-confirmation-step").is_present():
            self.q(css=".action-primary").click()
        else:
            raise Exception("The dashboard can only be accessed from the enrollment confirmation.")

        DashboardPage(self.browser).wait_for_page()


class FakePaymentPage(PageObject):
    """Interact with the fake payment endpoint.

    This page is hidden behind the feature flag `ENABLE_PAYMENT_FAKE`,
    which is enabled in the Bok Choy env settings.

    Configuring this payment endpoint also requires configuring the Bok Choy
    auth settings with the following:

        "CC_PROCESSOR_NAME": "CyberSource2",
        "CC_PROCESSOR": {
            "CyberSource2": {
                "SECRET_KEY": <string>,
                "ACCESS_KEY": <string>,
                "PROFILE_ID": "edx",
                "PURCHASE_ENDPOINT": "/shoppingcart/payment_fake"
            }
        }
    """
    def __init__(self, browser, course_id):
        """Initialize the page.

        Arguments:
            browser (Browser): The browser instance.
            course_id (unicode): The course in which the user is enrolling.
        """
        super(FakePaymentPage, self).__init__(browser)
        self._course_id = course_id

    url = BASE_URL + "/shoppingcart/payment_fake/"

    def is_browser_on_page(self):
        """Check if a step in the payment and verification flow has loaded."""
        message = self.q(css='BODY').text[0]
        match = re.search('Payment page', message)
        return True if match else False

    def submit_payment(self):
        """Interact with the payment submission button."""
        self.q(css="input[value='Submit']").click()

        return PaymentAndVerificationFlow(self.browser, self._course_id, entry_point='payment-confirmation').wait_for_page()


class FakeSoftwareSecureVerificationPage(PageObject):
    """
    This page is a page used for testing that allows the user to change the status of their most recent
    verification.
    """

    url = BASE_URL + '/verify_student/software-secure-fake-response'

    def __init__(self, browser):
        super(FakeSoftwareSecureVerificationPage, self).__init__(browser)

    def is_browser_on_page(self):
        """ Determine if browser is on the page. """
        message = self.q(css='BODY').text[0]
        match = re.search('Fake Software Secure page', message)
        return True if match else False

    def mark_approved(self):
        """ Mark the latest verification attempt as passing. """
        self.q(css='#btn_pass').click()

    def mark_denied(self):
        """ Mark the latest verification attempt as denied. """
        self.q(css='#btn_denied').click()

    def mark_error(self):
        """ Mark the latest verification attempt as an error. """
        self.q(css='#btn_error').click()

    def mark_unkown_error(self):
        """ Mark the latest verification attempt as an unknown error. """
        self.q(css='#btn_unkonwn_error').click()
