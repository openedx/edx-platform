from lettuce import world, step
from common import *
import time

from nose.tools import assert_equal
from nose.tools import assert_true

from selenium.webdriver.common.keys import Keys


############### ACTIONS ####################
@step('I select the Advanced Settings$')
def i_select_advanced_settings(step):
    expand_icon_css = 'li.nav-course-settings i.icon-expand'
    if world.browser.is_element_present_by_css(expand_icon_css):
        css_click(expand_icon_css)
    link_css = 'li.nav-course-settings-advanced a'
    css_click(link_css)


@step('I am on the Advanced Course Settings page in Studio$')
def i_am_on_advanced_course_settings(step):
    step.given('I have opened a new course in Studio')
    step.given('I select the Advanced Settings')


@step('I see only the display name$')
def i_see_only_display_name(step):
    assert_policy_entries(["display_name"], ['"Robot Super Course"'])


@step('I delete the display name')
def i_delete_the_display_name(step):
    delete_entry(0)
    click_save()


@step('there are no advanced policy settings$')
def no_policy_settings(step):
    assert_policy_entries([], [])


@step('create New Entries$')
def create_new_entries(step):
    create_entry("z", "apple")
    create_entry("a", "zebra")
    click_save()


@step('they are alphabetized$')
def they_are_alphabetized(step):
    assert_policy_entries(["a", "display_name", "z"], ['"zebra"', '"Robot Super Course"', '"apple"'])


@step('I create a JSON object$')
def create_JSON_object(step):
    create_entry("json", '{"key": "value", "key_2": "value_2"}')
    click_save()


@step('it is displayed as formatted$')
def it_is_formatted(step):
    assert_policy_entries(["display_name", "json"], ['"Robot Super Course"', '{\n    "key": "value",\n    "key_2": "value_2"\n}'])


# TODO: this is copied from terrain's step.py. Need to figure out how to share that code.
@step('I reload the page$')
def reload_the_page(step):
    world.browser.reload()


def create_entry(key, value):
    # Scroll down the page so the button is visible
    world.scroll_to_bottom()
    css_click_at('a.new-advanced-policy-item', 10, 10)
    new_key_css = 'div#__new_advanced_key__ input'
    new_key_element = css_find(new_key_css).first
    new_key_element.fill(key)
#   For some reason have to get the instance for each command (get error that it is no longer attached to the DOM)
#   Have to do all this because Selenium has a bug that fill does not remove existing text
    new_value_css = 'div.CodeMirror textarea'
    css_find(new_value_css).last.fill("")
    css_find(new_value_css).last._element.send_keys(Keys.DELETE, Keys.DELETE)
    css_find(new_value_css).last.fill(value)


def delete_entry(index):
    """ index is 0-based
    """
    css = '.delete-button'
    assert_true(world.browser.is_element_present_by_css(css, 5))
    delete_buttons = css_find(css)
    assert_true(len(delete_buttons) > index, "no delete button exists for entry " + str(index))
    delete_buttons[index].click()


def assert_policy_entries(expected_keys, expected_values):
    assert_entries('.key input', expected_keys)
    assert_entries('.json', expected_values)


def assert_entries(css, expected_values):
    webElements = css_find(css)
    assert_equal(len(expected_values), len(webElements))
#   Sometimes get stale reference if I hold on to the array of elements
    for counter in range(len(expected_values)):
        assert_equal(expected_values[counter], css_find(css)[counter].value)


def click_save():
    css = ".save-button"

    def is_shown(driver):
        visible = css_find(css).first.visible
        if visible:
            # Even when waiting for visible, this fails sporadically. Adding in a small wait.
            time.sleep(float(1))
        return visible
    wait_for(is_shown)
    css_click(css)


def fill_last_field(value):
    newValue = css_find('#__new_advanced_key__ input').first
    newValue.fill(value)
