"""
Container page in Studio
"""

from bok_choy.page_object import PageObject
from bok_choy.promise import Promise, EmptyPromise
from . import BASE_URL

from selenium.webdriver.common.action_chains import ActionChains

from utils import click_css, wait_for_notification, confirm_prompt


class ContainerPage(PageObject):
    """
    Container page in Studio
    """
    NAME_SELECTOR = '.page-header-title'
    NAME_INPUT_SELECTOR = '.page-header .xblock-field-input'
    NAME_FIELD_WRAPPER_SELECTOR = '.page-header .wrapper-xblock-field'

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

    def wait_for_component_menu(self):
        """
        Waits until the menu bar of components is present on the page.
        """
        EmptyPromise(
            lambda: self.q(css='div.add-xblock-component').present,
            'Wait for the menu of components to be present'
        ).fulfill()

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

    @property
    def publish_title(self):
        """
        Returns the title as displayed on the publishing sidebar component.
        """
        return self.q(css='.pub-status').first.text[0]

    @property
    def release_title(self):
        """
        Returns the title before the release date in the publishing sidebar component.
        """
        return self.q(css='.wrapper-release .title').first.text[0]

    @property
    def release_date(self):
        """
        Returns the release date of the unit (with ancestor inherited from), as displayed
        in the publishing sidebar component.
        """
        return self.q(css='.wrapper-release .copy').first.text[0]

    @property
    def last_saved_text(self):
        """
        Returns the last saved message as displayed in the publishing sidebar component.
        """
        return self.q(css='.wrapper-last-draft').first.text[0]

    @property
    def last_published_text(self):
        """
        Returns the last published message as displayed in the sidebar.
        """
        return self.q(css='.wrapper-last-publish').first.text[0]

    @property
    def currently_visible_to_students(self):
        """
        Returns True if the unit is marked as currently visible to students
        (meaning that a warning is being displayed).
        """
        warnings = self.q(css='.container-message .warning')
        if not warnings.is_present():
            return False
        warning_text = warnings.first.text[0]
        return warning_text == "Caution: The last published version of this unit is live. By publishing changes you will change the student experience."

    @property
    def publish_action(self):
        """
        Returns the link for publishing a unit.
        """
        return self.q(css='.action-publish').first

    def discard_changes(self):
        """
        Discards draft changes (which will then re-render the page).
        """
        click_css(self, 'a.action-discard', 0, require_notification=False)
        confirm_prompt(self)
        self.wait_for_ajax()

    @property
    def is_staff_locked(self):
        """ Returns True if staff lock is currently enabled, False otherwise """
        return 'icon-check' in self.q(css='a.action-staff-lock>i').attrs('class')

    def toggle_staff_lock(self):
        """
        Toggles "hide from students" which enables or disables a staff-only lock.

        Returns True if the lock is now enabled, else False.
        """
        was_locked_initially = self.is_staff_locked
        if not was_locked_initially:
            self.q(css='a.action-staff-lock').first.click()
        else:
            click_css(self, 'a.action-staff-lock', 0, require_notification=False)
            confirm_prompt(self)
        self.wait_for_ajax()
        return not was_locked_initially

    def view_published_version(self):
        """
        Clicks "View Live Version", which will open the published version of the unit page in the LMS.

        Switches the browser to the newly opened LMS window.
        """
        self.q(css='.button-view').first.click()
        self._switch_to_lms()

    def preview(self):
        """
        Clicks "Preview Changes", which will open the draft version of the unit page in the LMS.

        Switches the browser to the newly opened LMS window.
        """
        self.q(css='.button-preview').first.click()
        self._switch_to_lms()

    def _switch_to_lms(self):
        """
        Assumes LMS has opened-- switches to that window.
        """
        browser_window_handles = self.browser.window_handles
        # Switch to browser window that shows HTML Unit in LMS
        # The last handle represents the latest windows opened
        self.browser.switch_to_window(browser_window_handles[-1])

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

    def delete(self, source_index):
        """
        Delete the item with index source_index (based on vertical placement in page).
        Only visible items are counted in the source_index.
        The index of the first item is 0.
        """
        # Click the delete button
        click_css(self, 'a.delete-button', source_index, require_notification=False)
        # Click the confirmation dialog button
        confirm_prompt(self)

    def edit(self):
        """
        Clicks the "edit" button for the first component on the page.
        """
        return _click_edit(self)

    def add_missing_groups(self):
        """
        Click the "add missing groups" link.
        Note that this does an ajax call.
        """
        self.q(css='.add-missing-groups-button').first.click()
        self.wait_for_page()

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

    def is_inline_editing_display_name(self):
        """
        Return whether this container's display name is in its editable form.
        """
        return "is-editing" in self.q(css=self.NAME_FIELD_WRAPPER_SELECTOR).first.attrs("class")[0]


class XBlockWrapper(PageObject):
    """
    A PageObject representing a wrapper around an XBlock child shown on the Studio container page.
    """
    url = None
    BODY_SELECTOR = '.studio-xblock-wrapper'
    NAME_SELECTOR = '.xblock-display-name'
    COMPONENT_BUTTONS = {
        'advanced_tab': '.editor-tabs li.inner_tab_wrap:nth-child(2) > a',
        'save_settings': '.action-save',
    }

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
    def student_content(self):
        """
        Returns the text content of the xblock as displayed on the container page.
        """
        return self.q(css=self._bounded_selector('.xblock-student_view'))[0].text

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

    def go_to_container(self):
        """
        Open the container page linked to by this xblock, and return
        an initialized :class:`.ContainerPage` for that xblock.
        """
        return ContainerPage(self.browser, self.locator).visit()

    def edit(self):
        """
        Clicks the "edit" button for this xblock.
        """
        return _click_edit(self, self._bounded_selector)

    def open_advanced_tab(self):
        """
        Click on Advanced Tab.
        """
        self._click_button('advanced_tab')

    def save_settings(self):
        """
        Click on settings Save button.
        """
        self._click_button('save_settings')

    @property
    def editor_selector(self):
        return '.xblock-studio_view'

    def _click_button(self, button_name):
        """
        Click on a button as specified by `button_name`

        Arguments:
            button_name (str): button name

        """
        self.q(css=self.COMPONENT_BUTTONS[button_name]).first.click()
        self.wait_for_ajax()

    def go_to_group_configuration_page(self):
        """
        Go to the Group Configuration used by the component.
        """
        self.q(css=self._bounded_selector('span.message-text a')).first.click()

    @property
    def group_configuration_link_name(self):
        """
        Get Group Configuration name from link.
        """
        return self.q(css=self._bounded_selector('span.message-text a')).first.text[0]


def _click_edit(page_object, bounded_selector=lambda(x): x):
    """
    Click on the first edit button found and wait for the Studio editor to be present.
    """
    page_object.q(css=bounded_selector('.edit-button')).first.click()
    EmptyPromise(
        lambda: page_object.q(css='.xblock-studio_view').present,
        'Wait for the Studio editor to be present'
    ).fulfill()

    return page_object
