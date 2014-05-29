"""
Utility methods useful for Studio page tests.
"""
from bok_choy.promise import Promise
from selenium.webdriver.common.action_chains import ActionChains


def click_css(page, css, source_index=0, require_notification=True):
    """
    Click the button/link with the given css and index on the specified page (subclass of PageObject).

    If require_notification is False (default value is True), the method will return immediately.
    Otherwise, it will wait for the "mini-notification" to appear and disappear.
    """
    buttons = page.q(css=css)
    target = buttons[source_index]
    ActionChains(page.browser).click(target).release().perform()
    if require_notification:
        wait_for_notification(page)


def wait_for_notification(page):
    """
    Waits for the "mini-notification" to appear and disappear on the given page (subclass of PageObject).
    """
    def _is_saving():
        num_notifications = len(page.q(css='.wrapper-notification-mini.is-shown'))
        return (num_notifications == 1, num_notifications)

    def _is_saving_done():
        num_notifications = len(page.q(css='.wrapper-notification-mini.is-hiding'))
        return (num_notifications == 1, num_notifications)

    Promise(_is_saving, 'Notification showing.').fulfill()
    Promise(_is_saving_done, 'Notification hidden.').fulfill()
