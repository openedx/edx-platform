"""
Container page in Studio
"""

from bok_choy.page_object import PageObject
from bok_choy.promise import Promise, EmptyPromise
from . import BASE_URL

from selenium.webdriver.common.action_chains import ActionChains

from utils import click_css, wait_for_notification


class ContainerPage(PageObject):
    """
    Container page in Studio
    """
    NAME_SELECTOR = 'a.navigation-current'

    def __init__(self, browser, locator):
        super(ContainerPage, self).__init__(browser)
        self.locator = locator

    @property
    def url(self):
        """URL to the container page for an xblock."""
        return "{}/container/{}".format(BASE_URL, self.locator)

    @property
    def name(self):
        titles = self.q(css=self.NAME_SELECTOR).text
        if titles:
            return titles[0]
        else:
            return None

    def is_browser_on_page(self):

        def _is_finished_loading():
            # Wait until all components have been loaded.
            # See common/static/coffee/src/xblock/core.coffee which adds the
            # class "xblock-initialized" at the end of initializeBlock
            num_wrappers = len(self.q(css=XBlockWrapper.BODY_SELECTOR).results)
            num_xblocks_init = len(self.q(css='{} .xblock.xblock-initialized'.format(XBlockWrapper.BODY_SELECTOR)).results)
            is_done = num_wrappers == num_xblocks_init
            return (is_done, is_done)

        # First make sure that an element with the view-container class is present on the page,
        # and then wait for the loading spinner to go away and all the xblocks to be initialized.
        return (
            self.q(css='body.view-container').present and
            self.q(css='div.ui-loading.is-hidden').present and
            Promise(_is_finished_loading, 'Finished rendering the xblock wrappers.').fulfill()
        )

    @property
    def xblocks(self):
        """
        Return a list of xblocks loaded on the container page.
        """
        return self._get_xblocks()

    @property
    def inactive_xblocks(self):
        """
        Return a list of inactive xblocks loaded on the container page.
        """
        return self._get_xblocks(".is-inactive ")

    @property
    def active_xblocks(self):
        """
        Return a list of active xblocks loaded on the container page.
        """
        return self._get_xblocks(".is-active ")

    def _get_xblocks(self, prefix=""):
        return self.q(css=prefix + XBlockWrapper.BODY_SELECTOR).map(
            lambda el: XBlockWrapper(self.browser, el.get_attribute('data-locator'))).results

    def drag(self, source_index, target_index):
        """
        Gets the drag handle with index source_index (relative to the vertical layout of the page)
        and drags it to the location of the drag handle with target_index.

        This should drag the element with the source_index drag handle BEFORE the
        one with the target_index drag handle.
        """
        draggables = self.q(css='.drag-handle')
        source = draggables[source_index]
        target = draggables[target_index]
        action = ActionChains(self.browser)
        # When dragging before the target element, must take into account that the placeholder
        # will appear in the place where the target used to be.
        placeholder_height = 40
        action.click_and_hold(source).move_to_element_with_offset(
            target, 0, placeholder_height
        ).release().perform()
        wait_for_notification(self)

    def duplicate(self, source_index):
        """
        Duplicate the item with index source_index (based on vertical placement in page).
        """
        click_css(self, 'a.duplicate-button', source_index)

    def delete(self, group_index=0, xblock_index=0):
        """
        Delete the item with specified group and xblock indices (based on vertical placement in page).
        Note:
            Only visible items are counted.
            The index of the first item is 0.
        """
        # For the group index css, add 1 because nth-of-type is 1 based, and 1 more because
        # there is a hidden div.wrapper-group, before Active Groups and Inactive Groups
        # For the xblock index css, add 1 because nth-of-type is 1 based.
        css = 'div.wrapper-groups:nth-of-type({}) section.wrapper-xblock:nth-of-type({}) a.delete-button'.format(
            group_index + 2,
            xblock_index + 1
        )

        # Click the delete button
        click_css(self, css, 0, require_notification=False)

        # Wait for the warning prompt to appear
        self.wait_for_element_visibility('#prompt-warning', 'Deletion warning prompt is visible')

        # Make sure the delete button is there
        confirmation_button_css = '#prompt-warning a.button.action-primary'
        self.wait_for_element_visibility(confirmation_button_css, 'Confirmation dialog button is visible')

        # Click the confirmation dialog button
        click_css(self, confirmation_button_css, 0)

    def edit(self):
        """
        Clicks the "edit" button for the first component on the page.

        Same as the implementation in unit.py, unit and component pages will be merging.
        """
        self.q(css='.edit-button').first.click()
        EmptyPromise(
            lambda: self.q(css='.xblock-studio_view').present,
            'Wait for the Studio editor to be present'
        ).fulfill()

        return self

    def add_missing_groups(self):
        """
        Click the "add missing groups" link.
        Note that this does an ajax call.
        """
        self.q(css='.add-missing-groups-button').first.click()

    def missing_groups_button_present(self):
        """
        Returns True if the "add missing groups" button is present.
        """
        return self.q(css='.add-missing-groups-button').present

    def get_xblock_information_message(self):
        """
        Returns an information message for the container page.
        """
        return self.q(css=".xblock-message.information").first.text[0]


class XBlockWrapper(PageObject):
    """
    A PageObject representing a wrapper around an XBlock child shown on the Studio container page.
    """
    url = None
    BODY_SELECTOR = '.studio-xblock-wrapper'
    NAME_SELECTOR = '.header-details'

    def __init__(self, browser, locator):
        super(XBlockWrapper, self).__init__(browser)
        self.locator = locator

    def is_browser_on_page(self):
        return self.q(css='{}[data-locator="{}"]'.format(self.BODY_SELECTOR, self.locator)).present

    def _bounded_selector(self, selector):
        """
        Return `selector`, but limited to this particular `CourseOutlineChild` context
        """
        return '{}[data-locator="{}"] {}'.format(
            self.BODY_SELECTOR,
            self.locator,
            selector
        )

    @property
    def name(self):
        titles = self.q(css=self._bounded_selector(self.NAME_SELECTOR)).text
        if titles:
            return titles[0]
        else:
            return None

    @property
    def children(self):
        """
        Will return any first-generation descendant xblocks of this xblock.
        """
        descendants = self.q(css=self._bounded_selector(self.BODY_SELECTOR)).map(
            lambda el: XBlockWrapper(self.browser, el.get_attribute('data-locator'))).results

        # Now remove any non-direct descendants.
        grandkids = []
        for descendant in descendants:
            grandkids.extend(descendant.children)

        grand_locators = [grandkid.locator for grandkid in grandkids]
        return [descendant for descendant in descendants if not descendant.locator in grand_locators]

    @property
    def preview_selector(self):
        return self._bounded_selector('.xblock-student_view,.xblock-author_view')
