# disable missing docstring
# pylint: disable=missing-docstring

from lettuce import world
from nose.tools import assert_equal, assert_in
from terrain.steps import reload_the_page
from common import type_in_codemirror
from selenium.webdriver.common.keys import Keys


@world.absorb
def create_component_instance(step, category, component_type=None, is_advanced=False, advanced_component=None):
    """
    Create a new component in a Unit.

    Parameters
    ----------
    category: component type (discussion, html, problem, video, advanced)
    component_type: for components with multiple templates, the link text in the menu
    is_advanced: for problems, is the desired component under the advanced menu?
    advanced_component: for advanced components, the related value of policy key 'advanced_modules'
    """
    assert_in(category, ['advanced', 'problem', 'html', 'video', 'discussion'])

    component_button_css = 'span.large-{}-icon'.format(category.lower())
    if category == 'problem':
        module_css = 'div.xmodule_CapaModule'
    elif category == 'advanced':
        module_css = 'div.xmodule_{}Module'.format(advanced_component.title())
    elif category == 'discussion':
        module_css = 'div.xblock-author_view-{}'.format(category.lower())
    else:
        module_css = 'div.xmodule_{}Module'.format(category.title())

    # Count how many of that module is on the page. Later we will
    # assert that one more was added.
    # We need to use world.browser.find_by_css instead of world.css_find
    # because it's ok if there are currently zero of them.
    module_count_before = len(world.browser.find_by_css(module_css))

    # Disable the jquery animation for the transition to the menus.
    world.disable_jquery_animations()
    world.css_click(component_button_css)

    if category in ('problem', 'html', 'advanced'):
        world.wait_for_invisible(component_button_css)
        click_component_from_menu(category, component_type, is_advanced)

    expected_count = module_count_before + 1
    world.wait_for(
        lambda _: len(world.css_find(module_css)) == expected_count,
        timeout=20
    )


@world.absorb
def click_new_component_button(step, component_button_css):
    step.given('I have clicked the new unit button')

    world.css_click(component_button_css)


def _click_advanced():
    css = 'ul.problem-type-tabs a[href="#tab2"]'
    world.css_click(css)

    # Wait for the advanced tab items to be displayed
    tab2_css = 'div.ui-tabs-panel#tab2'
    world.wait_for_visible(tab2_css)


def _find_matching_button(category, component_type):
    """
    Find the button with the specified text. There should be one and only one.
    """

    # The tab shows buttons for the given category
    buttons = world.css_find('div.new-component-{} button'.format(category))

    # Find the button whose text matches what you're looking for
    matched_buttons = [btn for btn in buttons if btn.text == component_type]

    # There should be one and only one
    assert_equal(len(matched_buttons), 1)
    return matched_buttons[0]


def click_component_from_menu(category, component_type, is_advanced):
    """
    Creates a component for a category with more
    than one template, i.e. HTML and Problem.
    For some problem types, it is necessary to click to
    the Advanced tab.
    The component_type is the link text, e.g. "Blank Common Problem"
    """
    if is_advanced:
        # Sometimes this click does not work if you go too fast.
        world.retry_on_exception(
            _click_advanced,
            ignored_exceptions=AssertionError,
        )

    # Retry this in case the list is empty because you tried too fast.
    link = world.retry_on_exception(
        lambda: _find_matching_button(category, component_type),
        ignored_exceptions=AssertionError
    )

    # Wait for the link to be clickable. If you go too fast it is not.
    world.retry_on_exception(lambda: link.click())


@world.absorb
def edit_component_and_select_settings():
    world.edit_component()
    world.ensure_settings_visible()


@world.absorb
def ensure_settings_visible():
    # Select the 'settings' tab if there is one (it isn't displayed if it is the only option)
    settings_button = world.browser.find_by_css('.settings-button')
    if len(settings_button) > 0:
        world.css_click('.settings-button')


@world.absorb
def edit_component(index=0):
    # Verify that the "loading" indication has been hidden.
    world.wait_for_loading()
    # Verify that the "edit" button is present.
    world.wait_for(lambda _driver: world.css_visible('.edit-button'))
    world.css_click('.edit-button', index)
    world.wait_for_ajax_complete()


@world.absorb
def select_editor_tab(tab_name):
    editor_tabs = world.browser.find_by_css('.editor-tabs a')
    expected_tab_text = tab_name.strip().upper()
    matching_tabs = [tab for tab in editor_tabs if tab.text.upper() == expected_tab_text]
    assert len(matching_tabs) == 1
    tab = matching_tabs[0]
    tab.click()
    world.wait_for_ajax_complete()


def enter_xml_in_advanced_problem(step, text):
    """
    Edits an advanced problem (assumes only on page),
    types the provided XML, and saves the component.
    """
    world.edit_component()
    type_in_codemirror(0, text)
    world.save_component()


@world.absorb
def verify_setting_entry(setting, display_name, value, explicitly_set):
    """
    Verify the capa module fields are set as expected in the
    Advanced Settings editor.

    Parameters
    ----------
    setting: the WebDriverElement object found in the browser
    display_name: the string expected as the label
    html: the expected field value
    explicitly_set: True if the value is expected to have been explicitly set
        for the problem, rather than derived from the defaults. This is verified
        by the existence of a "Clear" button next to the field value.
    """
    label_element = setting.find_by_css('.setting-label')[0]
    assert_equal(display_name, label_element.html.strip())
    label_for = label_element['for']

    # Check if the web object is a list type
    # If so, we use a slightly different mechanism for determining its value
    if setting.has_class('metadata-list-enum') or setting.has_class('metadata-dict') or setting.has_class('metadata-video-translations'):
        list_value = ', '.join(ele.value for ele in setting.find_by_css('.list-settings-item'))
        assert_equal(value, list_value)
    elif setting.has_class('metadata-videolist-enum'):
        list_value = ', '.join(ele.find_by_css('input')[0].value for ele in setting.find_by_css('.videolist-settings-item'))
        assert_equal(value, list_value)
    else:
        assert_equal(value, setting.find_by_id(label_for).value)

    # VideoList doesn't have clear button
    if not setting.has_class('metadata-videolist-enum'):
        settingClearButton = setting.find_by_css('.setting-clear')[0]
        assert_equal(explicitly_set, settingClearButton.has_class('active'))
        assert_equal(not explicitly_set, settingClearButton.has_class('inactive'))


@world.absorb
def verify_all_setting_entries(expected_entries):
    settings = world.browser.find_by_css('.wrapper-comp-setting')
    assert_equal(len(expected_entries), len(settings))
    for (counter, setting) in enumerate(settings):
        world.verify_setting_entry(
            setting, expected_entries[counter][0],
            expected_entries[counter][1], expected_entries[counter][2]
        )


@world.absorb
def save_component():
    world.css_click("a.action-save,a.save-button")
    world.wait_for_ajax_complete()


@world.absorb
def save_component_and_reopen(step):
    save_component()
    # We have a known issue that modifications are still shown within the edit window after cancel (though)
    # they are not persisted. Refresh the browser to make sure the changes WERE persisted after Save.
    reload_the_page(step)
    edit_component_and_select_settings()


@world.absorb
def cancel_component(step):
    world.css_click("a.action-cancel")
    # We have a known issue that modifications are still shown within the edit window after cancel (though)
    # they are not persisted. Refresh the browser to make sure the changes were not persisted.
    reload_the_page(step)


@world.absorb
def revert_setting_entry(label):
    get_setting_entry(label).find_by_css('.setting-clear')[0].click()


@world.absorb
def get_setting_entry(label):
    def get_setting():
        settings = world.css_find('.wrapper-comp-setting')
        for setting in settings:
            if setting.find_by_css('.setting-label')[0].value == label:
                return setting
        return None
    return world.retry_on_exception(get_setting)


@world.absorb
def get_setting_entry_index(label):
    def get_index():
        settings = world.css_find('.wrapper-comp-setting')
        for index, setting in enumerate(settings):
            if setting.find_by_css('.setting-label')[0].value == label:
                return index
        return None
    return world.retry_on_exception(get_index)


@world.absorb
def set_field_value(index, value):
    """
    Set the field to the specified value.

    Note: we cannot use css_fill here because the value is not set
    until after you move away from that field.
    Instead we will find the element, set its value, then hit the Tab key
    to get to the next field.
    """
    elem = world.css_find('div.wrapper-comp-setting input')[index]
    elem.value = value
    elem.type(Keys.TAB)
