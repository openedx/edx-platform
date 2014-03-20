# disable missing docstring
# pylint: disable=C0111

from lettuce import world, step
from nose.tools import assert_in, assert_equal  # pylint: disable=no-name-in-module
from common import type_in_codemirror, get_codemirror_value


@step('I have created a Blank HTML Page$')
def i_created_blank_html_page(step):
    world.create_course_with_unit()
    world.create_component_instance(
        step=step,
        category='html',
        component_type='Text'
    )


@step('I see only the HTML display name setting$')
def i_see_only_the_html_display_name(step):
    world.verify_all_setting_entries([['Display Name', "Text", False]])


@step('I have created an E-text Written in LaTeX$')
def i_created_etext_in_latex(step):
    world.create_course_with_unit()
    step.given('I have enabled latex compiler')
    world.create_component_instance(
        step=step,
        category='html',
        component_type='E-text Written in LaTeX'
    )


@step('I edit the page$')
def i_click_on_edit_icon(step):
    world.edit_component()


@step('I add an image with a static link via the Image Plugin Icon$')
def i_click_on_image_plugin_icon(step):
    use_plugin(
        '.mce-i-image',
        lambda: world.css_fill('.mce-textbox', '/static/image.jpg', 0)
    )


@step('I add an link with a static link via the Link Plugin Icon$')
def i_click_on_link_plugin_icon(step):
    def fill_in_link_fields():
        world.css_fill('.mce-textbox', '/static/image.jpg', 0)
        world.css_fill('.mce-textbox', 'picture', 1)

    use_plugin('.mce-i-link', fill_in_link_fields)


@step('type "(.*)" in the code editor and press OK$')
def type_in_codemirror_plugin(step, text):
    use_plugin(
        '.mce-i-code',
        lambda: type_in_codemirror(0, text, "$('iframe').contents().find")
    )


@step('and the code editor displays "(.*)"$')
def verify_code_editor_text(step, text):
    use_plugin(
        '.mce-i-code',
        lambda: assert_equal(text, get_codemirror_value(0, "$('iframe').contents().find"))
    )


def use_plugin(button_class, action):
    # Click on plugin button
    world.css_click(button_class)

    # Wait for the editing window to open.
    world.wait_for_visible('.mce-window')

    # Trigger the action
    action()

    # Click OK
    world.css_click('.mce-primary')


@step('I save the page$')
def i_click_on_save(step):
    world.save_component(step)


@step('the page has text:')
def check_page_text(step):
    assert_equal(step.multiline, world.css_find('.xmodule_HtmlModule').html.strip())


@step('the image static link is rewritten to translate the path$')
def image_static_link_is_rewritten(step):
    # Find the TinyMCE iframe within the main window
    with world.browser.get_iframe('mce_0_ifr') as tinymce:
        image = tinymce.find_by_tag('img').first
        assert_in('c4x/MITx/999/asset/image.jpg', image['src'])


@step('the link static link is rewritten to translate the path$')
def link_static_link_is_rewritten(step):
    # Find the TinyMCE iframe within the main window
    with world.browser.get_iframe('mce_0_ifr') as tinymce:
        link = tinymce.find_by_tag('a').first
        assert_in('c4x/MITx/999/asset/image.jpg', link['href'])


@step('the expected toolbar buttons are displayed$')
def check_toolbar_buttons(step):
    dropdowns = world.css_find('.mce-listbox')
    assert_equal(2, len(dropdowns))

    # Format dropdown
    assert_equal('Paragraph', dropdowns[0].text)
    assert_equal('Font Family', dropdowns[1].text)

    # Font dropdown

    buttons = world.css_find('.mce-ico')

    assert_equal(14, len(buttons))

    def check_class(index, button_name):
        class_names = buttons[index]._element.get_attribute('class')
        assert_equal("mce-ico mce-i-" + button_name, class_names)

    check_class(0, 'bold')
    check_class(1, 'italic')
    # This is our custom "code style" button. It uses an image instead of a class.
    check_class(2, 'none')
    check_class(3, 'underline')
    check_class(4, 'forecolor')
    check_class(5, 'bullist')
    check_class(6, 'numlist')
    check_class(7, 'outdent')
    check_class(8, 'indent')
    check_class(9, 'blockquote')
    check_class(10, 'link')
    check_class(11, 'unlink')
    check_class(12, 'image')
    check_class(13, 'code')


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
