# disable missing docstring
# pylint: disable=C0111

from lettuce import world, step
from nose.tools import assert_in, assert_false, assert_true, assert_equal  # pylint: disable=no-name-in-module
from common import type_in_codemirror, get_codemirror_value

CODEMIRROR_SELECTOR_PREFIX = "$('iframe').contents().find"


@step('I have created a Blank HTML Page$')
def i_created_blank_html_page(step):
    step.given('I am in Studio editing a new unit')
    world.create_component_instance(
        step=step,
        category='html',
        component_type='Text'
    )


@step('I have created a raw HTML component')
def i_created_raw_html(step):
    step.given('I am in Studio editing a new unit')
    world.create_component_instance(
        step=step,
        category='html',
        component_type='Raw HTML'
    )


@step('I see the HTML component settings$')
def i_see_only_the_html_display_name(step):
    world.verify_all_setting_entries(
        [
            ['Display Name', "Text", False],
            ['Editor', "Visual", False]
        ]
    )


@step('I have created an E-text Written in LaTeX$')
def i_created_etext_in_latex(step):
    step.given('I am in Studio editing a new unit')
    step.given('I have enabled latex compiler')
    world.create_component_instance(
        step=step,
        category='html',
        component_type='E-text Written in LaTeX'
    )


@step('I edit the page$')
def i_click_on_edit_icon(step):
    world.edit_component()


@step('I add an image with static link "(.*)" via the Image Plugin Icon$')
def i_click_on_image_plugin_icon(step, path):
    use_plugin(
        '.mce-i-image',
        lambda: world.css_fill('.mce-textbox', path, 0)
    )


@step('the link is shown as "(.*)" in the Image Plugin$')
def check_link_in_image_plugin(step, path):
    use_plugin(
        '.mce-i-image',
        lambda: assert_equal(path, world.css_find('.mce-textbox')[0].value)
    )


@step('I add a link with static link "(.*)" via the Link Plugin Icon$')
def i_click_on_link_plugin_icon(step, path):
    def fill_in_link_fields():
        world.css_fill('.mce-textbox', path, 0)
        world.css_fill('.mce-textbox', 'picture', 1)

    use_plugin('.mce-i-link', fill_in_link_fields)


@step('the link is shown as "(.*)" in the Link Plugin$')
def check_link_in_link_plugin(step, path):
    # Ensure caret position is within the link just created.
    script = """
    var editor = tinyMCE.activeEditor;
    editor.selection.select(editor.dom.select('a')[0]);"""
    world.browser.driver.execute_script(script)
    world.wait_for_ajax_complete()

    use_plugin(
        '.mce-i-link',
        lambda: assert_equal(path, world.css_find('.mce-textbox')[0].value)
    )


@step('type "(.*)" in the code editor and press OK$')
def type_in_codemirror_plugin(step, text):
    # Verify that raw code editor is not visible.
    assert_true(world.css_has_class('.CodeMirror', 'is-inactive'))
    # Verify that TinyMCE editor is present
    assert_true(world.is_css_present('.tiny-mce'))
    use_code_editor(
        lambda: type_in_codemirror(0, text, CODEMIRROR_SELECTOR_PREFIX)
    )


@step('and the code editor displays "(.*)"$')
def verify_code_editor_text(step, text):
    use_code_editor(
        lambda: assert_equal(text, get_codemirror_value(0, CODEMIRROR_SELECTOR_PREFIX))
    )


def use_plugin(button_class, action):
    # Click on plugin button
    world.css_click(button_class)
    perform_action_in_plugin(action)


def use_code_editor(action):
    # Click on plugin button
    buttons = world.css_find('div.mce-widget>button')

    code_editor = [button for button in buttons if button.text == 'HTML']
    assert_equal(1, len(code_editor))
    code_editor[0].click()

    perform_action_in_plugin(action)


def perform_action_in_plugin(action):
     # Wait for the plugin window to open.
    world.wait_for_visible('.mce-window')

    # Trigger the action
    action()

    # Click OK
    world.css_click('.mce-primary')


@step('I save the page$')
def i_click_on_save(step):
    world.save_component()


@step('the page text contains:')
def check_page_text(step):
    assert_in(step.multiline, world.css_find('.xmodule_HtmlModule').html)


@step('the Raw Editor contains exactly:')
def check_raw_editor_text(step):
    assert_equal(step.multiline, get_codemirror_value(0))


@step('the src link is rewritten to "(.*)"$')
def image_static_link_is_rewritten(step, path):
    # Find the TinyMCE iframe within the main window
    with world.browser.get_iframe('mce_0_ifr') as tinymce:
        image = tinymce.find_by_tag('img').first
        assert_in(path, image['src'])


@step('the href link is rewritten to "(.*)"$')
def link_static_link_is_rewritten(step, path):
    # Find the TinyMCE iframe within the main window
    with world.browser.get_iframe('mce_0_ifr') as tinymce:
        link = tinymce.find_by_tag('a').first
        assert_in(path, link['href'])


@step('the expected toolbar buttons are displayed$')
def check_toolbar_buttons(step):
    dropdowns = world.css_find('.mce-listbox')
    assert_equal(2, len(dropdowns))

    # Format dropdown
    assert_equal('Paragraph', dropdowns[0].text)
    # Font dropdown
    assert_equal('Font Family', dropdowns[1].text)

    buttons = world.css_find('.mce-ico')

    # Note that the code editor icon is not present because we are now showing text instead of an icon.
    # However, other test points user the code editor, so we have already verified its presence.
    expected_buttons = [
        'bold',
        'italic',
        'underline',
        'forecolor',
        # This is our custom "code style" button, which uses an image instead of a class.
        'none',
        'bullist',
        'numlist',
        'outdent',
        'indent',
        'blockquote',
        'link',
        'unlink',
        'image'
    ]

    assert_equal(len(expected_buttons), len(buttons))

    for index, button in enumerate(expected_buttons):
        class_names = buttons[index]._element.get_attribute('class')
        assert_equal("mce-ico mce-i-" + button, class_names)


@step('I set the text to "(.*)" and I select the text$')
def set_text_and_select(step, text):
    script = """
    var editor = tinyMCE.activeEditor;
    editor.setContent(arguments[0]);
    editor.selection.select(editor.dom.select('p')[0]);"""
    world.browser.driver.execute_script(script, str(text))
    world.wait_for_ajax_complete()


@step('I select the code toolbar button$')
def select_code_button(step):
    # This is our custom "code style" button. It uses an image instead of a class.
    world.css_click(".mce-i-none")


@step('type "(.*)" into the Raw Editor$')
def type_in_raw_editor(step, text):
    # Verify that CodeMirror editor is not hidden
    assert_false(world.css_has_class('.CodeMirror', 'is-inactive'))
    # Verify that TinyMCE Editor is not present
    assert_true(world.is_css_not_present('.tiny-mce'))
    type_in_codemirror(0, text)


@step('I edit the component and select the (Raw|Visual) Editor$')
def select_editor(step, editor):
    world.edit_component_and_select_settings()
    world.browser.select('Editor', editor)
