"""
Utility methods useful for Studio page tests.
"""


from bok_choy.javascript import js_defined
from selenium.webdriver.common.keys import Keys

from common.test.acceptance.tests.helpers import click_and_wait_for_window

NAV_HELP_NOT_SIGNED_IN_CSS = '.nav-item.nav-not-signedin-help a'
NAV_HELP_CSS = '.nav-item.nav-account-help a'
SIDE_BAR_HELP_AS_LIST_ITEM = '.bit li.action-item a'
SIDE_BAR_HELP_CSS = '.external-help a, .external-help-button'


@js_defined('window.jQuery')
def type_in_codemirror(page, index, text, find_prefix="$"):
    script = u"""
    var cm = {find_prefix}('div.CodeMirror:eq({index})').get(0).CodeMirror;
    CodeMirror.signal(cm, "focus", cm);
    cm.setValue(arguments[0]);
    CodeMirror.signal(cm, "blur", cm);""".format(index=index, find_prefix=find_prefix)

    page.browser.execute_script(script, str(text))


@js_defined('window.jQuery')
def get_codemirror_value(page, index=0, find_prefix="$"):
    return page.browser.execute_script(
        u"return {find_prefix}('div.CodeMirror:eq({index})').get(0).CodeMirror.getValue();".format(
            index=index, find_prefix=find_prefix
        )
    )


def set_input_value(page, css, value):
    """
    Sets the text field with the given label (display name) to the specified value.
    """
    input_element = page.q(css=css).results[0]
    # Click in the input to give it the focus
    input_element.click()
    # Select all, then input the value
    input_element.send_keys(Keys.CONTROL + 'a')
    input_element.send_keys(value)
    # Return the input_element for chaining
    return input_element


def set_input_value_and_save(page, css, value):
    """
    Sets the text field with given label (display name) to the specified value, and presses Save.
    """
    set_input_value(page, css, value).send_keys(Keys.ENTER)
    page.wait_for_ajax()


def verify_ordering(test_class, page, expected_orderings):
    """
    Verifies the expected ordering of xblocks on the page.
    """
    xblocks = page.xblocks
    blocks_checked = set()
    for expected_ordering in expected_orderings:
        for xblock in xblocks:
            parent = list(expected_ordering.keys())[0]
            if xblock.name == parent:
                blocks_checked.add(parent)
                children = xblock.children
                expected_length = len(expected_ordering.get(parent))
                test_class.assertEqual(
                    expected_length, len(children),
                    u"Number of children incorrect for group {0}. Expected {1} but got {2}.".format(parent, expected_length, len(children)))
                for idx, expected in enumerate(expected_ordering.get(parent)):
                    test_class.assertEqual(expected, children[idx].name)
                    blocks_checked.add(expected)
                break
    test_class.assertEqual(len(blocks_checked), len(xblocks))


class HelpMixin(object):
    """
    Mixin for testing Help links.
    """
    def get_nav_help_element_and_click_help(self, signed_in=True):
        """
        Click on the help, and also get the DOM help element.

        It operates on the help elements in the navigation bar.

        Arguments:
            signed_in (bool): Indicates whether user is signed in or not.

        Returns:
            WebElement: Help DOM element in the navigation bar.
        """

        element_css = None
        if signed_in:
            element_css = NAV_HELP_CSS
        else:
            element_css = NAV_HELP_NOT_SIGNED_IN_CSS

        help_element = self.q(css=element_css).results[0]
        click_and_wait_for_window(self, help_element)
        return help_element

    def get_side_bar_help_element_and_click_help(self, as_list_item=False, index=-1):
        """
        Click on the help, and also get the DOM help element.

        It operates on the help elements in the side bar.

        Arguments:
            as_list_item (bool): Indicates whether help element is
                                 enclosed in a 'li' DOM element.
            index (int): The index of element in case there are more than
                         one matching elements.

        Returns:
            WebElement: Help DOM element in the side bar.
        """
        element_css = None
        if as_list_item:
            element_css = SIDE_BAR_HELP_AS_LIST_ITEM
        else:
            element_css = SIDE_BAR_HELP_CSS

        help_element = self.q(css=element_css).results[index]
        click_and_wait_for_window(self, help_element)
        return help_element
