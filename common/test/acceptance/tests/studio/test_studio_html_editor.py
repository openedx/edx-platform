"""
Acceptance tests for HTML component in studio
"""
from common.test.acceptance.tests.studio.base_studio_test import ContainerBase
from common.test.acceptance.fixtures.course import XBlockFixtureDesc
from common.test.acceptance.pages.studio.container import ContainerPage, XBlockWrapper
from common.test.acceptance.pages.studio.utils import add_component
from common.test.acceptance.pages.studio.html_component_editor import HtmlXBlockEditorView, HTMLEditorIframe


class HTMLComponentEditor(ContainerBase):
    """
    Feature: CMS.Component Adding
    As a course author, I want to be able to add and edit HTML component
    """
    def setUp(self, is_staff=True):
        """
        Create a course with a section, subsection, and unit to which to add the component.
        """
        super(HTMLComponentEditor, self).setUp(is_staff=is_staff)
        self.component = 'Text'
        self.unit = self.go_to_unit_page()
        self.container_page = ContainerPage(self.browser, None)
        self.xblock_wrapper = XBlockWrapper(self.browser, None)
        # Add HTML component
        add_component(self.container_page, 'html', self.component)
        self.component = self.unit.xblocks[1]
        self.container_page.edit()
        self.html_editor = HtmlXBlockEditorView(self.browser, self.component.locator)
        self.iframe = HTMLEditorIframe(self.browser, self.component.locator)

    def populate_course_fixture(self, course_fixture):
        """
        Adds a course fixture
        """
        course_fixture.add_children(
            XBlockFixtureDesc('chapter', 'Test Section').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection').add_children(
                    XBlockFixtureDesc('vertical', 'Test Unit')
                )
            )
        )

    def test_user_can_view_metadata(self):
        """
        Scenario: User can view metadata
        Given I have created a Blank HTML Page
            And I edit and select Settings
                Then I see the HTML component settings
        """
        self.html_editor.open_settings_tab()
        display_name_value = self.html_editor.get_default_settings()[0]
        display_name_key = self.html_editor.keys[0]
        self.assertEqual(
            ['Display Name', 'Text'],
            [display_name_key, display_name_value],
            "Settings not found"
        )
        editor_value = self.html_editor.get_default_settings()[1]
        editor_key = self.html_editor.keys[1]
        self.assertEqual(
            ['Editor', 'Visual'],
            [editor_key, editor_value],
            "Settings not found"
        )

    def test_user_can_modify_display_name(self):
        """
        Scenario: User can modify display name
        Given I have created a Blank HTML Page
            And I edit and select Settings
        Then I can modify the display name
            And my display name change is persisted on save
        """
        self.html_editor.open_settings_tab()
        self.html_editor.set_field_val('Display Name', 'New Name')
        self.html_editor.save_settings()
        component_name = self.unit.xblock_titles[0]
        self.assertEqual(component_name, 'New Name', "Component name is not as edited")

    def test_link_plugin_sets_url_correctly(self):
        """
        Scenario: TinyMCE link plugin sets urls correctly
        Given I have created a Blank HTML Page
            When I edit the page
            And I add a link with static link "/static/image.jpg" via the Link Plugin Icon
                Then the href link is rewritten to the asset link "image.jpg"
                And the link is shown as "/static/image.jpg" in the Link Plugin
        """
        static_link = '/static/image.jpg'
        self.html_editor.open_link_plugin()
        self.html_editor.save_static_link(static_link)
        self.html_editor.switch_to_iframe()
        href = self.iframe.href
        self.assertIn('image.jpg', href)
        self.iframe.select_link()
        self.iframe.switch_to_default()
        self.assertEqual(
            self.html_editor.url_from_the_link_plugin,
            static_link,
            "URL in the link plugin is different"
        )
