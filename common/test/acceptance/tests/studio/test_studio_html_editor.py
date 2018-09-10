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
        # Add Discussion component
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

    def _content_test(self, content_to_verify):
        content = content_to_verify
        self.html_editor.set_content_and_save(content)
        self.container_page.wait_for_page()
        xmodule_html = self.container_page.html_for_htmlmodule
        self.assertIn(content, xmodule_html)

    def test_user_can_view_metadata(self):
        """
        Scenario: User can view metadata
        Given I have created a Blank HTML Page
            And I edit and select Settings
                Then I see the HTML component settings
        """
        self.html_editor.open_settings_tab()
        display_name = self.html_editor.get_default_settings()[0]
        display_name_key = self.html_editor.keys[0]
        self.assertEqual(
            ['Display Name', 'Text'],
            [display_name_key, display_name],
            "Settings not found"
        )
        editor_name = self.html_editor.get_default_settings()[1]
        editor_key = self.html_editor.keys[1]
        self.assertEqual(
            ['Editor', 'Visual'],
            [editor_key, editor_name],
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
        self.html_editor.open_link_plugin()
        self.html_editor.save_static_link('/static/image.jpg')
        self.html_editor.switch_to_iframe()
        href = self.iframe.href
        self.assertIn('image.jpg', href)
        self.iframe.click_link_and_switch_to_default()
        self.assertEqual(
            self.html_editor.url_from_the_link_plugin,
            '/static/image.jpg',
            "URL in the link plugin is different"
        )

    def test_tinymce_and_codemirror_preserve_style_tags(self):
        """
        Scenario: TinyMCE and CodeMirror preserve style tags
        Given I have created a Blank HTML Page
            When I edit the page
            And type "<p class='title'>pages</p><style><!-- .title { color: red; } --></style>" in the code editor and
            press OK
            And I save the page
                Then the page text contains:
                  ""
                  <p class="title">pages</p>
                  <style><!--
                  .title { color: red; }
                  --></style>
                  ""
        """
        content = "<p class='title'>pages</p><style><!-- .title { color: red; } --></style>"
        self._content_test(content)

    def test_tinymce_and_codemirror_preserve_span_tags(self):
        """
        Scenario: TinyMCE and CodeMirror preserve span tags
        Given I have created a Blank HTML Page
            When I edit the page
            And type "<span>Test</span>" in the code editor and press OK
            And I save the page
                Then the page text contains:
                ""
                    <span>Test</span>
                ""
        """
        content = "<span>Test</span>"
        self._content_test(content)

    def test_tinymce_and_codemirror_preserve_math_tags(self):
        """
        Scenario: TinyMCE and CodeMirror preserve math tags
        Given I have created a Blank HTML Page
            When I edit the page
            And type "<math><msup><mi>x</mi><mn>2</mn></msup></math>" in the code editor and press OK
            And I save the page
                Then the page text contains:
                ""
                    <math><msup><mi>x</mi><mn>2</mn></msup></math>
                ""
        """
        content = "<math><msup><mi>x</mi><mn>2</mn></msup></math>"
        self._content_test(content)

    def test_code_format_toolbar_wraps_text_with_code_tags(self):
        """
        Scenario: Code format toolbar button wraps text with code tags
        Given I have created a Blank HTML Page
            When I edit the page
            And I set the text to "display as code" and I select the text
            And I save the page
                Then the page text contains:
                ""
                    <p><code>display as code</code></p>
                ""
        """
        self.html_editor.set_text_and_select("display as code")
        self.html_editor.save_settings()
        xmodule_html = self.container_page.html_for_htmlmodule
        self.assertIn('<p><code>display as code</code></p>', xmodule_html)

    def test_raw_hmlcomponent_does_not_change_text(self):
        """
        Scenario: Raw HTML component does not change text
        Given I have created a raw HTML component
            When I edit the page
            And type "<li>zzzz<ol> " into the Raw Editor
            And I save the page
                Then the page text contains:
                  ""
                  <li>zzzz<ol>
                  ""
            And I edit the page
                Then the Raw Editor contains exactly:
                  ""
                  <li>zzzz<ol>
                  ""
        """
        content = "<li>zzzz<ol>"
        self.html_editor.set_content_and_save(content, raw=True)
        xmodule_html = self.container_page.html_for_htmlmodule
        self.assertIn("<li>zzzz<ol>", xmodule_html)
        self.container_page.edit()
        self.html_editor.open_raw_editor()
        editor_value = self.html_editor.editor_value
        self.assertEqual(content, editor_value)

    def test_tinymce_toolbar_buttons_are_as_expected(self):
        """
        Scenario: TinyMCE toolbar buttons are as expected
        Given I have created a Blank HTML Page
        When I edit the page
            Then the expected toolbar buttons are displayed
        """
        expected_buttons = [
            u'bold',
            u'italic',
            u'underline',
            u'forecolor',
            # This is our custom "code style" button, which uses an image instead of a class.
            u'none',
            u'alignleft',
            u'aligncenter',
            u'alignright',
            u'alignjustify',
            u'bullist',
            u'numlist',
            u'outdent',
            u'indent',
            u'blockquote',
            u'link',
            u'unlink',
            u'image'
        ]
        toolbar_dropdowns = self.html_editor.toolbar_dropdown_titles
        self.assertEqual(len(toolbar_dropdowns), 2)
        self.assertEqual(['Paragraph', 'Font Family'], toolbar_dropdowns)
        toolbar_buttons = self.html_editor.toolbar_button_titles
        self.assertEqual(len(toolbar_buttons), len(expected_buttons))

        for index, button in enumerate(expected_buttons):
            class_name = toolbar_buttons[index]
            self.assert_equal("mce-ico mce-i-" + button, class_name)

    def test_static_links_converted(self):
        """
        Scenario: Static links are converted when switching between code editor and WYSIWYG views
        Given I have created a Blank HTML Page
        When I edit the page
            And type "<img src="/static/image.jpg">" in the code editor and press OK
        Then the src link is rewritten to the asset link "image.jpg"
            And the code editor displays "<p><img src="/static/image.jpg" /></p>"
        """
        self._content_test('<img src="/static/image.jpg">')
        self.html_editor.set_content_and_save('<img src="/static/image.jpg">')
        self.container_page.edit()
        # add jquery function here

    def test_font_selection_dropdown(self):
        """
        Scenario: Font selection dropdown contains Default font and tinyMCE builtin fonts
        Given I have created a Blank HTML Page
        When I edit the page
        And I click font selection dropdown
            Then I should see a list of available fonts
            And "Default" fonts should be available
            And all standard tinyMCE fonts should be available
        """
        EXPECTED_FONTS = {
            u"Default": [u'"Open Sans"', u'Verdana', u'Arial', u'Helvetica', u'sans-serif'],
            u"Andale Mono": [u'andale mono', u'times'],
            u"Arial": [u'arial', u'helvetica', u'sans-serif'],
            u"Arial Black": [u'arial black', u'avant garde'],
            u"Book Antiqua": [u'book antiqua', u'palatino'],
            u"Comic Sans MS": [u'comic sans ms', u'sans-serif'],
            u"Courier New": [u'courier new', u'courier'],
            u"Georgia": [u'georgia', u'palatino'],
            u"Helvetica": [u'helvetica'],
            u"Impact": [u'impact', u'chicago'],
            u"Symbol": [u'symbol'],
            u"Tahoma": [u'tahoma', u'arial', u'helvetica', u'sans-serif'],
            u"Terminal": [u'terminal', u'monaco'],
            u"Times New Roman": [u'times new roman', u'times'],
            u"Trebuchet MS": [u'trebuchet ms', u'geneva'],
            u"Verdana": [u'verdana', u'geneva'],
            # tinyMCE does not set font-family on dropdown span for these two fonts
            u"Webdings": [u""],  # webdings
            u"Wingdings": [u""]  # wingdings
        }
        self.html_editor.open_font_dropdown()
        self.assertDictContainsSubset(self.html_editor.font_dict(), EXPECTED_FONTS)