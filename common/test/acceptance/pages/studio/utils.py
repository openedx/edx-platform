"""
Utility methods useful for Studio page tests.
"""
from bok_choy.promise import Promise
from selenium.webdriver.common.action_chains import ActionChains


def click_css(page, css, source_index=0, require_notification=True):
    """
    Click the button/link with the given css and index on the specified page (subclass of PageObject).

    Will only consider buttons with a non-zero size.

    If require_notification is False (default value is True), the method will return immediately.
    Otherwise, it will wait for the "mini-notification" to appear and disappear.
    """
    buttons = page.q(css=css).filter(lambda el: el.size['width'] > 0)
    target = buttons[source_index]
    ActionChains(page.browser).click(target).release().perform()
    if require_notification:
        wait_for_notification(page)


def wait_for_notification(page):
    """
    Waits for the "mini-notification" to appear and disappear on the given page (subclass of PageObject).
    """
    def _is_saving():
        num_notifications = page.q(css='.wrapper-notification-mini.is-shown').present
        return (num_notifications == 1, num_notifications)

    def _is_saving_done():
        num_notifications = page.q(css='.wrapper-notification-mini.is-hiding').present
        return (num_notifications == 1, num_notifications)

    Promise(_is_saving, 'Notification should have been shown.', timeout=60).fulfill()
    Promise(_is_saving_done, 'Notification should have been hidden.', timeout=60).fulfill()


def press_the_notification_button(page, name):
    # Because the notification uses a CSS transition,
    # Selenium will always report it as being visible.
    # This makes it very difficult to successfully click
    # the "Save" button at the UI level.
    # Instead, we use JavaScript to reliably click
    # the button.
    btn_css = 'div#page-notification a.action-%s' % name.lower()
    page.browser.execute_script("$('{}').focus().click()".format(btn_css))
    page.wait_for_ajax()


def add_discussion(page, menu_index):
    """
    Add a new instance of the discussion category.

    menu_index specifies which instance of the menus should be used (based on vertical
    placement within the page).
    """
    click_css(page, 'a>span.large-discussion-icon', menu_index)


def add_advanced_component(page, menu_index, name):
    """
    Adds an instance of the advanced component with the specified name.

    menu_index specifies which instance of the menus should be used (based on vertical
    placement within the page).
    """
    click_css(page, 'a>span.large-advanced-icon', menu_index, require_notification=False)

    # Sporadically, the advanced component was not getting created after the click_css call on the category (below).
    # Try making sure that the menu of advanced components is visible before clicking (the HTML is always on the
    # page, but will have display none until the large-advanced-icon is clicked).
    def is_advanced_components_showing():
        advanced_buttons = page.q(css=".new-component-advanced").filter(lambda el: el.size['width'] > 0)
        return (len(advanced_buttons) == 1, len(advanced_buttons))

    Promise(is_advanced_components_showing, "Advanced component menu not showing").fulfill()

    click_css(page, 'a[data-category={}]'.format(name))


def type_in_codemirror(page, index, text, find_prefix="$"):
    script = """
    var cm = {find_prefix}('div.CodeMirror:eq({index})').get(0).CodeMirror;
    CodeMirror.signal(cm, "focus", cm);
    cm.setValue(arguments[0]);
    CodeMirror.signal(cm, "blur", cm);""".format(index=index, find_prefix=find_prefix)
    page.browser.execute_script(script, str(text))


def get_codemirror_value(page, index=0, find_prefix="$"):
    return page.browser.execute_script(
        """
        return {find_prefix}('div.CodeMirror:eq({index})').get(0).CodeMirror.getValue();
        """.format(index=index, find_prefix=find_prefix)
    )
