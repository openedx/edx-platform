"""
Container page in Studio
"""

from bok_choy.page_object import PageObject
from bok_choy.promise import Promise
from . import BASE_URL

from selenium.webdriver.common.action_chains import ActionChains


class ContainerPage(PageObject):
    """
    Container page in Studio
    """

    def __init__(self, browser, unit_locator):
        super(ContainerPage, self).__init__(browser)
        self.unit_locator = unit_locator

    @property
    def url(self):
        """URL to the container page for an xblock."""
        return "{}/container/{}".format(BASE_URL, self.unit_locator)

    def is_browser_on_page(self):

        def _is_finished_loading():
            # Wait until all components have been loaded
            is_done = len(self.q(css=XBlockWrapper.BODY_SELECTOR).results) == len(
                self.q(css='{} .xblock'.format(XBlockWrapper.BODY_SELECTOR)).results)
            return (is_done, is_done)

        # First make sure that an element with the view-container class is present on the page,
        # and then wait to make sure that the xblocks are all there.
        return (
            self.q(css='body.view-container').present and
            Promise(_is_finished_loading, 'Finished rendering the xblock wrappers.').fulfill()
        )

    @property
    def xblocks(self):
        """
        Return a list of xblocks loaded on the container page.
        """
        return self.q(css=XBlockWrapper.BODY_SELECTOR).map(
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
        self.wait_for_notification()

    def add_discussion(self, menu_index):
        """
        Add a new instance of the discussion category.

        menu_index specifies which instance of the menus should be used (based on vertical
        placement within the page).
        """
        self.click('a>span.large-discussion-icon', menu_index)

    def duplicate(self, source_index):
        """
        Duplicate the item with index source_index (based on vertical placement in page).
        """
        self.click('a.duplicate-button', source_index)

    def delete(self, source_index):
        """
        Delete the item with index source_index (based on vertical placement in page).
        """
        self.click('a.delete-button', source_index, wait_for_notification=False)
        # Click the confirmation dialog button
        self.click('a.button.action-primary', 0)

    def click(self, css, source_index, wait_for_notification=True):
        """
        Click the button/link with the given css and index.

        If wait_for_notification is False (default value is True), the method will return immediately.
        Otherwise, it will wait for the "mini-notification" to appear and disappear.
        """
        buttons = self.q(css=css)
        target = buttons[source_index]
        ActionChains(self.browser).click(target).release().perform()
        if wait_for_notification:
            self.wait_for_notification()

    def wait_for_notification(self):
        """
        Waits for the "mini-notification" to appear and disapper.
        """
        def _is_saving():
            num_notifications = len(self.q(css='.wrapper-notification-mini.is-shown'))
            return (num_notifications == 1, num_notifications)

        def _is_saving_done():
            num_notifications = len(self.q(css='.wrapper-notification-mini.is-hiding'))
            return (num_notifications == 1, num_notifications)

        Promise(_is_saving, 'Notification showing.').fulfill()
        Promise(_is_saving_done, 'Notification hidden.').fulfill()


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
        return self._bounded_selector('.xblock-student_view')
