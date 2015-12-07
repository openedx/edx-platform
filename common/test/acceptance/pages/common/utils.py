"""
Utility methods common to Studio and the LMS.
"""
from bok_choy.promise import EmptyPromise
from ...tests.helpers import disable_animations


def wait_for_notification(page):
    """
    Waits for the "mini-notification" to appear and disappear on the given page (subclass of PageObject).
    """
    def _is_saving():
        """Whether or not the notification is currently showing."""
        return page.q(css='.wrapper-notification-mini.is-shown').present

    def _is_saving_done():
        """Whether or not the notification is finished showing."""
        return page.q(css='.wrapper-notification-mini.is-hiding').present

    EmptyPromise(_is_saving, 'Notification should have been shown.', timeout=60).fulfill()
    EmptyPromise(_is_saving_done, 'Notification should have been hidden.', timeout=60).fulfill()


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
        return element.is_displayed() and all(size > 0 for size in element.size.itervalues())

    # Disable all animations for faster testing with more reliable synchronization
    disable_animations(page)
    # Click on the element in the browser
    page.q(css=css).filter(_is_visible).nth(source_index).click()

    if require_notification:
        wait_for_notification(page)

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
    page.wait_for_element_visibility(
        '.wrapper-prompt:focus',
        'Prompt is in focus'
    )
    confirmation_button_css = '.prompt .action-' + ('secondary' if cancel else 'primary')
    page.wait_for_element_visibility(confirmation_button_css, 'Confirmation button is visible')
    require_notification = (not cancel) if require_notification is None else require_notification
    click_css(page, confirmation_button_css, require_notification=require_notification)
