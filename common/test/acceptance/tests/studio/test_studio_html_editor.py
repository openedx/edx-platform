"""
Acceptance tests for HTML component in studio
"""


import os

from common.test.acceptance.fixtures.course import XBlockFixtureDesc
from common.test.acceptance.pages.studio.container import ContainerPage, XBlockWrapper
from common.test.acceptance.pages.studio.html_component_editor import HTMLEditorIframe, HtmlXBlockEditorView
from common.test.acceptance.pages.studio.utils import add_component, type_in_codemirror
from common.test.acceptance.tests.studio.base_studio_test import ContainerBase

UPLOAD_SUFFIX = 'data/uploads/studio-uploads/'
UPLOAD_FILE_DIR = os.path.abspath(os.path.join(__file__, '../../../../', UPLOAD_SUFFIX))


class HTMLComponentEditorTests(ContainerBase):
    """
    Feature: CMS.Component Adding
    As a course author, I want to be able to add and edit HTML component
    """
    shard = 15

    def setUp(self, is_staff=True):
        """
        Create a course with a section, subsection, and unit to which to add the component.
        """
        super(HTMLComponentEditorTests, self).setUp(is_staff=is_staff)
        self.unit = self.go_to_unit_page()
        self.container_page = ContainerPage(self.browser, None)
        self.xblock_wrapper = XBlockWrapper(self.browser, None)
        self.component = None
        self.html_editor = None
        self.iframe = None

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

    def _add_content(self, content):
        """
        Set and save content in editor and assert its presence in container page's html

        Args:
            content(str): Verifiable content
        """
        self.html_editor.set_raw_content(content)
        self.html_editor.save_content()
        self.container_page.wait_for_page()

    def _add_component(self, sub_type):
        """
        Add sub-type of HTML component in studio

        Args:
            sub_type(str): Sub-type of HTML component
        """
        add_component(self.container_page, 'html', sub_type)
        self.component = self.unit.xblocks[1]
        self.html_editor = HtmlXBlockEditorView(self.browser, self.component.locator)
        self.iframe = HTMLEditorIframe(self.browser, self.component.locator)

    def test_user_can_view_metadata(self):
        """
        Scenario: User can view metadata
        Given I have created a Blank HTML Page
            And I edit and select Settings
                Then I see the HTML component settings
        """

        # Add HTML Text type component
        self._add_component('Text')
        self.container_page.edit()
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
        # Add HTML Text type component
        self._add_component('Text')
        self.container_page.edit()
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

        # Add HTML Text type component
        self._add_component('Text')
        self.container_page.edit()
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
        content = u'<p class="title">pages</p><style><!-- .title { color: red; } --></style>'

        # Add HTML Text type component
        self._add_component('Text')
        self.container_page.edit()
        self._add_content(content)
        html = self.container_page.content_html
        self.assertIn(content, html)

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

        # Add HTML Text type component
        self._add_component('Text')
        self.container_page.edit()
        self._add_content(content)
        html = self.container_page.content_html
        self.assertIn(content, html)

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

        # Add HTML Text type component
        self._add_component('Text')
        self.container_page.edit()
        self._add_content(content)
        html = self.container_page.content_html
        self.assertIn(content, html)

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
        # Add HTML Text type component
        self._add_component('Text')
        self.container_page.edit()
        self.html_editor.set_text_and_select("display as code")
        self.html_editor.click_code_toolbar_button()
        self.html_editor.save_content()
        html = self.container_page.content_html
        self.assertIn(html, '<p><code>display as code</code></p>')

    def test_raw_html_component_does_not_change_text(self):
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
        content = "<li>zzzz</li>"

        # Add Raw HTML type component
        self._add_component('Raw HTML')
        self.container_page.edit()

        # Set content in tinymce editor
        type_in_codemirror(self.html_editor, 0, content)
        self.html_editor.save_content()

        # The HTML of the content added through tinymce editor
        html = self.container_page.content_html
        # The text content should be present with its tag preserved
        self.assertIn(content, html)

        self.container_page.edit()
        editor_value = self.html_editor.editor_value
        # The tinymce editor value should not be different from the content added in the start
        self.assertEqual(content, editor_value)

    def test_tinymce_toolbar_buttons_are_as_expected(self):
        """
        Scenario: TinyMCE toolbar buttons are as expected
        Given I have created a Blank HTML Page
        When I edit the page
            Then the expected toolbar buttons are displayed
        """
        # Add HTML Text type component
        self._add_component('Text')
        self.container_page.edit()

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
        # The toolbar is divided in two sections: drop-downs and all other formatting buttons
        # The assertions under asserts for the drop-downs
        self.assertEqual(len(toolbar_dropdowns), 2)
        self.assertEqual(['Paragraph', 'Font Family'], toolbar_dropdowns)

        toolbar_buttons = self.html_editor.toolbar_button_titles
        # The assertions under asserts for all the remaining formatting buttons
        self.assertEqual(len(toolbar_buttons), len(expected_buttons))

        for index, button in enumerate(expected_buttons):
            class_name = toolbar_buttons[index]
            self.assertEqual("mce-ico mce-i-" + button, class_name)

    def test_static_links_converted(self):
        """
        Scenario: Static links are converted when switching between code editor and WYSIWYG views
        Given I have created a Blank HTML Page
        When I edit the page
            And type "<img src="/static/image.jpg">" in the code editor and press OK
        Then the src link is rewritten to the asset link /asset-v1:(course_id)+type@asset+block/image.jpg
            And the code editor displays "<p><img src="/static/image.jpg" /></p>"
        """
        value = '<img src="/static/image.jpg">'

        # Add HTML Text type component
        self._add_component('Text')
        self.container_page.edit()
        self.html_editor.set_raw_content(value)
        self.html_editor.save_content()
        html = self.container_page.content_html
        src = "/asset-v1:{}+type@asset+block/image.jpg".format(self.course_id.strip('course-v1:'))
        self.assertIn(src, html)
        self.container_page.edit()
        self.html_editor.open_raw_editor()
        editor_value = self.html_editor.editor_value
        self.assertEqual(value, editor_value)

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
        # Add HTML Text type component
        self._add_component('Text')
        self.container_page.edit()
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
        self.assertDictContainsSubset(EXPECTED_FONTS, self.html_editor.font_dict())

    def test_image_modal(self):
        """
        Scenario: TinyMCE text editor allows to add multiple images.

        Given I have created a Blank text editor Page.
        I add an image in TinyMCE text editor and hit save button.
        I edit the component again.
        I add another image in TinyMCE text editor and hit save button again.
            Then it is expected that both images show up on page.
        """
        image_file_names = [u'file-0.png', u'file-1.png']
        self._add_component('Text')

        for image in image_file_names:
            image_path = os.path.join(UPLOAD_FILE_DIR, image)
            self.container_page.edit()
            self.html_editor.open_image_modal()
            self.html_editor.upload_image(image_path)
            self.html_editor.save_content()
            self.html_editor.wait_for_ajax()

        self.container_page.edit()
        self.html_editor.open_raw_editor()
        editor_value = self.html_editor.editor_value
        number_of_images = editor_value.count(u'img')
        self.assertEqual(number_of_images, 2)
