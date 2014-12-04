"""
Library edit page in Studio
"""

from bok_choy.page_object import PageObject
from selenium.webdriver.common.keys import Keys
from .container import XBlockWrapper
from ...tests.helpers import disable_animations
from .utils import confirm_prompt, wait_for_notification
from . import BASE_URL


class LibraryPage(PageObject):
    """
    Library page in Studio
    """

    def __init__(self, browser, locator):
        super(LibraryPage, self).__init__(browser)
        self.locator = locator

    @property
    def url(self):
        """
        URL to the library edit page for the given library.
        """
        return "{}/library/{}".format(BASE_URL, unicode(self.locator))

    def is_browser_on_page(self):
        """
        Returns True iff the browser has loaded the library edit page.
        """
        return self.q(css='body.view-library').present

    def get_header_title(self):
        """
        The text of the main heading (H1) visible on the page.
        """
        return self.q(css='h1.page-header-title').text

    def wait_until_ready(self):
        """
        When the page first loads, there is a loading indicator and most
        functionality is not yet available. This waits for that loading to
        finish.

        Always call this before using the page. It also disables animations
        for improved test reliability.
        """
        self.wait_for_ajax()
        self.wait_for_element_invisibility('.ui-loading', 'Wait for the page to complete its initial loading of XBlocks via AJAX')
        disable_animations(self)

    @property
    def xblocks(self):
        """
        Return a list of xblocks loaded on the container page.
        """
        return self._get_xblocks()

    def click_duplicate_button(self, xblock_id):
        """
        Click on the duplicate button for the given XBlock
        """
        self._action_btn_for_xblock_id(xblock_id, "duplicate").click()
        wait_for_notification(self)
        self.wait_for_ajax()

    def click_delete_button(self, xblock_id, confirm=True):
        """
        Click on the delete button for the given XBlock
        """
        self._action_btn_for_xblock_id(xblock_id, "delete").click()
        if confirm:
            confirm_prompt(self)  # this will also wait_for_notification()
            self.wait_for_ajax()

    def nav_disabled(self, position, arrows=('next', 'previous')):
        """
        Verifies that pagination nav is disabled. Position can be 'top' or 'bottom'.

        To specify a specific arrow, pass an iterable with a single element, 'next' or 'previous'.
        """
        return all([
            self.q(css='nav.%s * a.%s-page-link.is-disabled' % (position, arrow))
            for arrow in arrows
        ])

    def move_back(self, position):
        """
        Clicks one of the forward nav buttons. Position can be 'top' or 'bottom'.
        """
        self.q(css='nav.%s * a.previous-page-link' % position)[0].click()
        self.wait_until_ready()

    def move_forward(self, position):
        """
        Clicks one of the forward nav buttons. Position can be 'top' or 'bottom'.
        """
        self.q(css='nav.%s * a.next-page-link' % position)[0].click()
        self.wait_until_ready()

    def revisit(self):
        """
        Visit the page's URL, instead of refreshing, so that a new state is created.
        """
        self.browser.get(self.browser.current_url)
        self.wait_until_ready()

    def go_to_page(self, number):
        """
        Enter a number into the page number input field, and then try to navigate to it.
        """
        page_input = self.q(css="#page-number-input")[0]
        page_input.click()
        page_input.send_keys(str(number))
        page_input.send_keys(Keys.RETURN)
        self.wait_until_ready()

    def check_page_unchanged(self, first_block_name):
        """
        Used to make sure that a page has not transitioned after a bogus number is given.
        """
        if not self.xblocks[0].name == first_block_name:
            return False
        if not self.q(css='#page-number-input')[0].get_attribute('value') == '':
            return False
        return True

    def _get_xblocks(self):
        """
        Create an XBlockWrapper for each XBlock div found on the page.
        """
        prefix = '.wrapper-xblock.level-page '
        return self.q(css=prefix + XBlockWrapper.BODY_SELECTOR).map(lambda el: XBlockWrapper(self.browser, el.get_attribute('data-locator'))).results

    def _div_for_xblock_id(self, xblock_id):
        """
        Given an XBlock's usage locator as a string, return the WebElement for
        that block's wrapper div.
        """
        return self.q(css='.wrapper-xblock.level-page .studio-xblock-wrapper').filter(lambda el: el.get_attribute('data-locator') == xblock_id)

    def _action_btn_for_xblock_id(self, xblock_id, action):
        """
        Given an XBlock's usage locator as a string, return one of its action
        buttons.
        action is 'edit', 'duplicate', or 'delete'
        """
        return self._div_for_xblock_id(xblock_id)[0].find_element_by_css_selector('.header-actions .{action}-button.action-button'.format(action=action))
