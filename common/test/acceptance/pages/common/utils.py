"""
Utility methods common to Studio and the LMS.
"""


import six
from bok_choy.promise import BrokenPromise
from selenium.webdriver.common.action_chains import ActionChains

from common.test.acceptance.pages.lms.create_mode import ModeCreationPage
from common.test.acceptance.pages.lms.pay_and_verify import FakePaymentPage, PaymentAndVerificationFlow
from common.test.acceptance.pages.lms.track_selection import TrackSelectionPage
from common.test.acceptance.tests.helpers import disable_animations


def sync_on_notification(page, style='default', wait_for_hide=False):
    """
    Sync on notifications but do not raise errors.

    A BrokenPromise in the wait_for probably means that we missed it.
    We should just swallow this error and not raise it for reasons including:
    * We are not specifically testing this functionality
    * This functionality is covered by unit tests
    * This verification method is prone to flakiness
      and browser version dependencies

    See classes in edx-platform:
     lms/static/sass/elements/_system-feedback.scss
    """
    hiding_class = 'is-hiding'
    shown_class = 'is-shown'

    def notification_has_class(style, el_class):
        """
        Return a boolean representing whether
        the notification has the class applied.
        """
        if style == 'mini':
            css_string = '.wrapper-notification-mini.{}'
        else:
            css_string = '.wrapper-notification-confirmation.{}'
        return page.q(css=css_string.format(el_class)).present

    # Wait for the notification to show.
    # This notification appears very quickly and maybe missed. Don't raise an error.
    try:
        page.wait_for(
            lambda: notification_has_class(style, shown_class),
            'Notification should have been shown.',
            timeout=5
        )
    except BrokenPromise as _err:
        pass

    # Now wait for it to hide.
    # This is not required for web page interaction, so not really needed.
    if wait_for_hide:
        page.wait_for(
            lambda: notification_has_class(style, hiding_class),
            'Notification should have hidden.'
        )


def click_css(page, css, source_index=0, require_notification=True):
    """
    Click the button/link with the given css and index on the specified page (subclass of PageObject).

    Will only consider elements that are displayed and have a height and width greater than zero.

    If require_notification is False (default value is True), the method will return immediately.
    Otherwise, it will wait for the "mini-notification" to appear and disappear.
    """
    def _is_visible(element):
        """Is the given element visible?"""
        # Only make the call to size once (instead of once for the height and once for the width)
        # because otherwise you will trigger a extra query on a remote element.
        return element.is_displayed() and all(size > 0 for size in six.itervalues(element.size))

    # Disable all animations for faster testing with more reliable synchronization
    disable_animations(page)
    # Click on the element in the browser
    page.q(css=css).filter(_is_visible).nth(source_index).click()

    if require_notification:
        sync_on_notification(page)

    # Some buttons trigger ajax posts
    # (e.g. .add-missing-groups-button as configured in split_test_author_view.js)
    # so after you click anything wait for the ajax call to finish
    page.wait_for_ajax()


def confirm_prompt(page, cancel=False, require_notification=None):
    """
    Ensures that a modal prompt and confirmation button are visible, then clicks the button. The prompt is canceled iff
    cancel is True.
    """
    page.wait_for_element_visibility('.prompt', 'Prompt is visible')
    confirmation_button_css = '.prompt .action-' + ('secondary' if cancel else 'primary')
    page.wait_for_element_visibility(confirmation_button_css, 'Confirmation button is visible')
    require_notification = (not cancel) if require_notification is None else require_notification
    click_css(page, confirmation_button_css, require_notification=require_notification)


def hover(browser, element):
    """
    Hover over an element.
    """
    ActionChains(browser).move_to_element(element).perform()


def enroll_user_track(browser, course_id, track):
    """
    Utility method to enroll a user in the audit or verified user track.  Creates and connects to the
    necessary pages. Selects the track and handles payment for verified.
    Supported tracks are 'verified' or 'audit'.
    """
    payment_and_verification_flow = PaymentAndVerificationFlow(browser, course_id)
    fake_payment_page = FakePaymentPage(browser, course_id)
    track_selection = TrackSelectionPage(browser, course_id)

    # Select track and process payment
    track_selection.visit()
    track_selection.enroll(track)
    if track == 'verified':
        payment_and_verification_flow.proceed_to_payment()
        fake_payment_page.submit_payment()


def add_enrollment_course_modes(browser, course_id, tracks):
    """
    Add the specified array of tracks to the given course.
    Supported tracks are `verified` and `audit` (all others will be ignored),
    and display names assigned are `Verified` and `Audit`, respectively.
    """
    for track in tracks:
        if track == 'audit':
            # Add an audit mode to the course
            ModeCreationPage(
                browser,
                course_id, mode_slug='audit',
                mode_display_name='Audit'
            ).visit()

        elif track == 'verified':
            # Add a verified mode to the course
            ModeCreationPage(
                browser, course_id, mode_slug='verified',
                mode_display_name='Verified', min_price=10
            ).visit()
