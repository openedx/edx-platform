"""
Pages page for a course.
"""
from common.test.acceptance.pages.common.utils import click_css, confirm_prompt
from common.test.acceptance.pages.studio.course_page import CoursePage
from bok_choy.promise import EmptyPromise
from selenium.webdriver import ActionChains


class PagesPage(CoursePage):
    """
    Pages page for a course.
    """

    url_path = "tabs"

    def is_browser_on_page(self):
        return self.q(css='body.view-static-pages').present

    def is_static_page_present(self):
        """
        Checks for static tab's presence

        Returns:
             bool: True if present
        """
        return self.q(css='.wrapper.wrapper-component-action-header').present

    def add_static_page(self):
        """
        Adds a static page
        """
        total_tabs = len(self.q(css='.course-nav-list>li'))
        click_css(self, '.add-pages .new-tab', require_notification=False)
        self.wait_for(
            lambda: len(self.q(css='.course-nav-list>li')) == total_tabs + 1,
            description="Static tab is added"
        )
        self.wait_for_element_visibility(
            '.tab-list :nth-child({}) .xblock-student_view'.format(total_tabs),
            'Static tab is visible'
        )
        # self.wait_for_ajax()

    def delete_static_tab(self):
        """
        Deletes a static page
        """
        click_css(self, '.btn-default.delete-button.action-button', require_notification=False)
        confirm_prompt(self)

    def click_edit_static_page(self):
        """
        Clicks on edit button to open up the xblock modal
        """
        self.q(css='.edit-button').first.click()
        EmptyPromise(
            lambda: self.q(css='.xblock-studio_view').present,
            'Wait for the Studio editor to be present'
        ).fulfill()

    def drag_and_drop_first_static_page_to_last(self):
        """
        Drags and drops the first the static page to the last
        """
        draggable_elements = self.q(css='.component .drag-handle').results
        source_element = draggable_elements[0]
        target_element = self.q(css='.new-component-item').results[0]
        action = ActionChains(self.browser)
        action.drag_and_drop(source_element, target_element).perform()
        self.wait_for_ajax()

    def drag_and_drop(self, default_tab=False):
        """
        Drags and drops the first static page to the last
        """
        css_selector = '.component .drag-handle'
        if default_tab:
            css_selector = '.drag-handle.action'
        source_element = self.q(css=css_selector).results[0]
        target_element = self.q(css='.new-component-item').results[0]
        action = ActionChains(self.browser)
        action.drag_and_drop(source_element, target_element).perform()
        self.wait_for_ajax()

    @property
    def static_tab_titles(self):
        """
        Return titles of all static tabs
        Returns:
            list: list of all the titles
        """
        self.wait_for_element_visibility(
            '.wrapper-component-action-header .component-actions',
            "Tab's edit button is visible"
        )
        return self.q(css='div.xmodule_StaticTabModule').text

    @property
    def built_in_page_titles(self):
        """
        Gets the default tab title
        Returns:
            list: list of all the titles
        """
        return self.q(css='.course-nav-list.ui-sortable h3').text

    def open_settings_tab(self):
        """
        Clicks settings tab
        """
        self.q(css='.editor-modes .settings-button').first.click()
        self.wait_for_ajax()

    def is_tab_visible(self, tab_name):
        """
        Checks for the tab's visibility
        Args:
            tab_name(string): Name of the tab for which visibility is to be checked
        Returns:
            true(bool): if tab is visible
            false(bool): if tab is not visible
        """
        css_selector = '[data-tab-id="{}"] .toggle-checkbox'.format(tab_name)
        return True if not self.q(css=css_selector).selected else False

    def toggle_tab(self, tab_name):
        """
        Toggles the visibility on tab
        Args:
            tab_name(string): Name of the tab to be toggled
        """
        css_selector = '[data-tab-id="{}"] .action-visible'.format(tab_name)
        return self.q(css=css_selector).first.click()

    def set_field_val(self, field_display_name, field_value):
        """
        Set the value of a field in editor

        Arguments:
            field_display_name(str): Display name of the field for which the value is to be changed
            field_value(str): New value for the field
        """
        selector = '.xblock-studio_view li.field label:contains("{}") + input'.format(field_display_name)
        script = '$(arguments[0]).val(arguments[1]).change();'
        self.browser.execute_script(script, selector, field_value)

    def save(self):
        """
        Clicks save button.
        """
        click_css(self, '.action-save')

    def refresh_and_wait_for_load(self):
        """
        Refresh the page and wait for all resources to load.
        """
        self.browser.refresh()
        self.wait_for_page()
