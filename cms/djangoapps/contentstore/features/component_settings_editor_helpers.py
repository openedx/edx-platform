# disable missing docstring
#pylint: disable=C0111

from lettuce import world
from nose.tools import assert_equal
from terrain.steps import reload_the_page


@world.absorb
def create_component_instance(step, component_button_css, instance_id, expected_css):
    click_new_component_button(step, component_button_css)
    click_component_from_menu(instance_id, expected_css)


@world.absorb
def click_new_component_button(step, component_button_css):
    step.given('I have opened a new course section in Studio')
    step.given('I have added a new subsection')
    step.given('I expand the first section')
    world.css_click('a.new-unit-item')
    world.css_click(component_button_css)


@world.absorb
def click_component_from_menu(instance_id, expected_css):
    elem_css = "a[data-location='%s']" % instance_id
    assert_equal(1, len(world.css_find(elem_css)))
    world.css_click(elem_css)
    assert_equal(1, len(world.css_find(expected_css)))

@world.absorb
def edit_component_and_select_settings():
    world.css_click('a.edit-button')
    world.css_click('#settings-mode')


@world.absorb
def verify_setting_entry(setting, display_name, value, explicitly_set):
    assert_equal(display_name, setting.find_by_css('.setting-label')[0].value)
    assert_equal(value, setting.find_by_css('.setting-input')[0].value)
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
def save_component_and_reopen(step):
    world.css_click("a.save-button")
    # We have a known issue that modifications are still shown within the edit window after cancel (though)
    # they are not persisted. Refresh the browser to make sure the changes WERE persisted after Save.
    reload_the_page(step)
    edit_component_and_select_settings()


@world.absorb
def cancel_component(step):
    world.css_click("a.cancel-button")
    # We have a known issue that modifications are still shown within the edit window after cancel (though)
    # they are not persisted. Refresh the browser to make sure the changes were not persisted.
    reload_the_page(step)


@world.absorb
def revert_setting_entry(label):
    get_setting_entry(label).find_by_css('.setting-clear')[0].click()


@world.absorb
def get_setting_entry(label):
    settings = world.browser.find_by_css('.wrapper-comp-setting')
    for setting in settings:
        if setting.find_by_css('.setting-label')[0].value == label:
            return setting
    return None
