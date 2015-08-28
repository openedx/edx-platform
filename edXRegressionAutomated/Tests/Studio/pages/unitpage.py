from bok_choy.page_object import PageObject
from bok_choy.javascript import wait_for_js

class UnitsPage(PageObject):
    """
    Units page of Auto course (Add New Component)
    """
    url = None

    def is_browser_on_page(self):
        return 'unit' in self.browser.title.lower()

    def click_unit_discussion_button(self):
        # Click Discussion Unit in Add New Components

        self.q(css='.content-primary').first.click()
        self.wait_for_element_presence('.large-discussion-icon', 'Cannot find Discussion button')
        self.q(css='.large-discussion-icon').first.click()
        self.wait_for_element_presence('.xmodule_DiscussionModule.xblock-initialized', 'Inline Discussion')

    def click_unit_html_button(self):
        # Click HTML unit in Add New Components

        self.wait_for_element_presence('.large-html-icon', 'Cannot find add components html button')
        self.q(css='.large-html-icon').first.click()
        self.wait_for_element_presence('.new-component-html', 'Html component options')

    def click_unit_common_problem_button(self):
        # Click Problem unit then Common Problem Type in Add New Components

        self.q(css='.large-problem-icon').first.click()
        self.wait_for_element_presence('.new-component-problem', 'Problem component options')
        self.q(css='a#ui-id-1.link-tab.ui-tabs-anchor').first.click()

    def click_unit_advanced_problem_button(self):
        # Click Problem unit then Advanced in Add New Components

        self.q(css='.large-problem-icon').first.click()
        self.wait_for_element_presence('.new-component-problem', 'Problem component options')
        self.q(css='a#ui-id-2.link-tab.ui-tabs-anchor').first.click()

    def add_component_html(self, component):
        # Add Html Units

        self.q(css='.new-component-html a[data-boilerplate='+ component + ']').click()
        self.wait_for_element_presence('.editor-md', 'New component')

    def add_component_common_problem(self, component):
        # Add Problem Units

        self.q(css='.new-component-problem a[data-boilerplate='+ component + ']').click()
        self.wait_for_element_presence('.editor-md', 'New component')

    @wait_for_js
    def verify_component(self, component):
        # Verify added Html and Problem Units on pages

        self.wait_for_element_visibility('.wrapper-xblock.level-element', 'Component')
        self.wait_for_element_visibility('.edit-button.action-button', 'X Block')
        added_components = self.q(css='.xblock-display-name')
        for added_component in added_components:
            if added_component.text == component:
                return True

    def click_unit_video_button(self):
        # Click Video Unit in Add New Components

        self.q(css='.content-primary').first.click()
        self.wait_for_element_presence('.large-video-icon', 'Video button')
        self.q(css='.large-video-icon').first.click()
        self.wait_for_element_presence('.xmodule_VideoModule.xblock-initialized', 'Added Video')

    def delete_component(self):
        # Delete the added component
        self.wait_for_element_visibility('.wrapper-xblock.level-element', 'Component')
        self.q(css='.wrapper-xblock.level-element .delete-button.action-button').click()
        self.wait_for_element_visibility('.button.action-primary', 'Delete Unit Pop up')
        self.q(css='.button.action-primary').click()

    def click_publish_button(self):
        # Click Publish button
        self.q(css='.action-publish.action-primary').first.click()
        self.wait_for_ajax()

    def click_view_live_version_button_and_go_to_lms(self):
        # Click View Live Version button and verify added components on pages
        self.q(css='.button-view.action-button span.action-button-text').first.click()
        self.browser.switch_to_window(self.browser.window_handles[-1])
        self.wait_for_page()

    def edit_html_text(self, edit_text):
        # Edit HTML Text component
        self.q(css='.edit-button.action-button span.action-button-text').first.click()
        self.q(css='#tinymce').first.click()
        #self.q(css='.mce-content-body p').fill('Edited html text')
        self.browser.find_element_by_css_selector('#tinymce').send_keys(edit_text)
        self.q(css='action-save').first.click()
        self.wait_for_ajax()

    def verify_html_text_lms(self):
        # Verify HTML Text on pages
        return self.q(css='.vert.vert-0').text[0]
