"""
Container page in Studio
"""

from bok_choy.page_object import PageObject
from bok_choy.promise import Promise, EmptyPromise
from common.test.acceptance.pages.studio import BASE_URL
from common.test.acceptance.pages.studio.utils import HelpMixin

from common.test.acceptance.pages.common.utils import click_css, confirm_prompt

from common.test.acceptance.pages.studio.utils import type_in_codemirror


class ContainerPage(PageObject, HelpMixin):
    """
    Container page in Studio
    """
    NAME_SELECTOR = '.page-header-title'
    NAME_INPUT_SELECTOR = '.page-header .xblock-field-input'
    NAME_FIELD_WRAPPER_SELECTOR = '.page-header .wrapper-xblock-field'
    ADD_MISSING_GROUPS_SELECTOR = '.notification-action-button[data-notification-action="add-missing-groups"]'

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
        def _xblock_count(class_name, request_token):
            return len(self.q(css='{body_selector} .xblock.{class_name}[data-request-token="{request_token}"]'.format(
                body_selector=XBlockWrapper.BODY_SELECTOR, class_name=class_name, request_token=request_token
            )).results)

        def _is_finished_loading():
            is_done = False
            # Get the request token of the first xblock rendered on the page and assume it is correct.
            data_request_elements = self.q(css='[data-request-token]')
            if len(data_request_elements) > 0:
                request_token = data_request_elements.first.attrs('data-request-token')[0]
                # Then find the number of Studio xblock wrappers on the page with that request token.
                num_wrappers = len(self.q(css='{} [data-request-token="{}"]'.format(XBlockWrapper.BODY_SELECTOR, request_token)).results)
                # Wait until all components have been loaded and marked as either initialized or failed.
                # See:
                #   - common/static/js/xblock/core.js which adds the class "xblock-initialized"
                #     at the end of initializeBlock.
                #   - common/static/js/views/xblock.js which adds the class "xblock-initialization-failed"
                #     if the xblock threw an error while initializing.
                num_initialized_xblocks = _xblock_count('xblock-initialized', request_token)
                num_failed_xblocks = _xblock_count('xblock-initialization-failed', request_token)
                is_done = num_wrappers == (num_initialized_xblocks + num_failed_xblocks)
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

    def shows_inherited_staff_lock(self, parent_type=None, parent_name=None):
        """
        Returns True if the unit inherits staff lock from a section or subsection.
        """
        return self.q(css='.bit-publishing .wrapper-visibility .copy .inherited-from').visible

    @property
    def sidebar_visibility_message(self):
        """
        Returns the text within the sidebar visibility section.
        """
        return self.q(css='.bit-publishing .wrapper-visibility').first.text[0]

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
        for attr in self.q(css='a.action-staff-lock>.fa').attrs('class'):
            if 'fa-check-square-o' in attr:
                return True
        return False

    def toggle_staff_lock(self, inherits_staff_lock=False):
        """
        Toggles "hide from students" which enables or disables a staff-only lock.

        Returns True if the lock is now enabled, else False.
        """
        was_locked_initially = self.is_staff_locked
        if not was_locked_initially:
            self.q(css='a.action-staff-lock').first.click()
        else:
            click_css(self, 'a.action-staff-lock', 0, require_notification=False)
            if not inherits_staff_lock:
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
        Clicks "Preview", which will open the draft version of the unit page in the LMS.

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
        return _click_edit(self, '.edit-button', '.xblock-studio_view')

    def add_missing_groups(self):
        """
        Click the "add missing groups" link.
        Note that this does an ajax call.
        """
        self.q(css=self.ADD_MISSING_GROUPS_SELECTOR).first.click()
        self.wait_for_ajax()

        # Wait until all xblocks rendered.
        self.wait_for_page()

    def missing_groups_button_present(self):
        """
        Returns True if the "add missing groups" button is present.
        """
        return self.q(css=self.ADD_MISSING_GROUPS_SELECTOR).present

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

    def get_category_tab_names(self, category_type):
        """
        Returns list of tab name in a category.

        Arguments:
            category_type (str): category type

        Returns:
            list
        """
        self.q(css='.add-xblock-component-button[data-type={}]'.format(category_type)).first.click()
        return self.q(css='.{}-type-tabs>li>a'.format(category_type)).text

    def get_category_tab_components(self, category_type, tab_index):
        """
        Return list of component names in a tab in a category.

        Arguments:
            category_type (str): category type
            tab_index (int): tab index in a category

        Returns:
            list
        """
        css = '#tab{tab_index} button[data-category={category_type}] span'.format(
            tab_index=tab_index,
            category_type=category_type
        )
        return self.q(css=css).html


class XBlockWrapper(PageObject):
    """
    A PageObject representing a wrapper around an XBlock child shown on the Studio container page.
    """
    url = None
    BODY_SELECTOR = '.studio-xblock-wrapper'
    NAME_SELECTOR = '.xblock-display-name'
    VALIDATION_SELECTOR = '.xblock-message.validation'
    COMPONENT_BUTTONS = {
        'basic_tab': '.editor-tabs li.inner_tab_wrap:nth-child(1) > a',
        'advanced_tab': '.editor-tabs li.inner_tab_wrap:nth-child(2) > a',
        'settings_tab': '.editor-modes .settings-button',
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
    def author_content(self):
        """
        Returns the text content of the xblock as displayed on the container page.
        (For blocks which implement a distinct author_view).
        """
        return self.q(css=self._bounded_selector('.xblock-author_view'))[0].text

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
        return [descendant for descendant in descendants if descendant.locator not in grand_locators]

    @property
    def has_validation_message(self):
        """ Is a validation warning/error/message shown? """
        return self.q(css=self._bounded_selector(self.VALIDATION_SELECTOR)).present

    def _validation_paragraph(self, css_class):
        """ Helper method to return the <p> element of a validation warning """
        return self.q(css=self._bounded_selector('{} p.{}'.format(self.VALIDATION_SELECTOR, css_class)))

    @property
    def has_validation_warning(self):
        """ Is a validation warning shown? """
        return self._validation_paragraph('warning').present

    @property
    def has_validation_error(self):
        """ Is a validation error shown? """
        return self._validation_paragraph('error').present

    @property
    # pylint: disable=invalid-name
    def has_validation_not_configured_warning(self):
        """ Is a validation "not configured" message shown? """
        return self._validation_paragraph('not-configured').present

    @property
    def validation_warning_text(self):
        """ Get the text of the validation warning. """
        return self._validation_paragraph('warning').text[0]

    @property
    def validation_error_text(self):
        """ Get the text of the validation error. """
        return self._validation_paragraph('error').text[0]

    @property
    def validation_error_messages(self):
        return self.q(css=self._bounded_selector('{} .xblock-message-item.error'.format(self.VALIDATION_SELECTOR))).text

    @property
    # pylint: disable=invalid-name
    def validation_not_configured_warning_text(self):
        """ Get the text of the validation "not configured" message. """
        return self._validation_paragraph('not-configured').text[0]

    @property
    def preview_selector(self):
        return self._bounded_selector('.xblock-student_view,.xblock-author_view')

    @property
    def has_group_visibility_set(self):
        return self.q(css=self._bounded_selector('.wrapper-xblock.has-group-visibility-set')).is_present()

    @property
    def has_duplicate_button(self):
        """
        Returns true if this xblock has a 'duplicate' button
        """
        return self.q(css=self._bounded_selector('a.duplicate-button'))

    @property
    def has_delete_button(self):
        """
        Returns true if this xblock has a 'delete' button
        """
        return self.q(css=self._bounded_selector('a.delete-button'))

    @property
    def has_edit_visibility_button(self):
        """
        Returns true if this xblock has an 'edit visibility' button
        :return:
        """
        return self.q(css=self._bounded_selector('.visibility-button')).is_present()

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
        return _click_edit(self, '.edit-button', '.xblock-studio_view', self._bounded_selector)

    def edit_visibility(self):
        """
        Clicks the edit visibility button for this xblock.
        """
        return _click_edit(self, '.visibility-button', '.xblock-visibility_view', self._bounded_selector)

    def open_advanced_tab(self):
        """
        Click on Advanced Tab.
        """
        self._click_button('advanced_tab')

    def open_basic_tab(self):
        """
        Click on Basic Tab.
        """
        self._click_button('basic_tab')

    def open_settings_tab(self):
        """
        If editing, click on the "Settings" tab
        """
        self._click_button('settings_tab')

    def set_field_val(self, field_display_name, field_value):
        """
        If editing, set the value of a field.
        """
        selector = '{} li.field label:contains("{}") + input'.format(self.editor_selector, field_display_name)
        script = "$(arguments[0]).val(arguments[1]).change();"
        self.browser.execute_script(script, selector, field_value)

    def reset_field_val(self, field_display_name):
        """
        If editing, reset the value of a field to its default.
        """
        scope = '{} li.field label:contains("{}")'.format(self.editor_selector, field_display_name)
        script = "$(arguments[0]).siblings('.setting-clear').click();"
        self.browser.execute_script(script, scope)

    def set_codemirror_text(self, text, index=0):
        """
        Set the text of a CodeMirror editor that is part of this xblock's settings.
        """
        type_in_codemirror(self, index, text, find_prefix='$("{}").find'.format(self.editor_selector))

    def set_license(self, license_type):
        """
        Uses the UI to set the course's license to the given license_type (str)
        """
        css_selector = (
            "ul.license-types li[data-license={license_type}] button"
        ).format(license_type=license_type)
        self.wait_for_element_presence(
            css_selector,
            "{license_type} button is present".format(license_type=license_type)
        )
        self.q(css=css_selector).click()

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

    def is_placeholder(self):
        """
        Checks to see if the XBlock is rendered as a placeholder without a preview.
        """
        return not self.q(css=self._bounded_selector('.wrapper-xblock article')).present

    @property
    def group_configuration_link_name(self):
        """
        Get Group Configuration name from link.
        """
        return self.q(css=self._bounded_selector('span.message-text a')).first.text[0]


def _click_edit(page_object, button_css, view_css, bounded_selector=lambda(x): x):
    """
    Click on the first editing button found and wait for the Studio editor to be present.
    """
    page_object.q(css=bounded_selector(button_css)).first.click()
    EmptyPromise(
        lambda: page_object.q(css=view_css).present,
        'Wait for the Studio editor to be present'
    ).fulfill()

    return page_object
