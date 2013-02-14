from lettuce import world, step
from common import *
import time

from nose.tools import assert_equal
from nose.tools import assert_true

from selenium.webdriver.common.keys import Keys


############### ACTIONS ####################
@step('I select the Advanced Settings$')
def i_select_advanced_settings(step):
    link_css = 'a#settings-tab'
    css_click(link_css)
    link_css = "[data-section='advanced']"
    css_click(link_css)

@step('I refresh and select the Advanced Settings$')
def refresh_and_select_advanced_settings(step):
    reload()
    i_select_advanced_settings(step)

@step('I see only the display name$')
def i_see_only_display_name(step):
    assert_policy_entries(["display_name"], ['"Robot Super Course"'])

@step('I delete the display name')
def i_delete_the_display_name(step):
    delete_entry(0)
    click_save()

@step("There are no advanced policy settings$")
def no_policy_settings(step):
    assert_policy_entries([], [])

@step("Create New Entries")
def create_new_entries(step):
    create_entry("z", "apple")
    create_entry("a", "zebra")
    click_save()

@step("They are alphabetized")
def they_are_alphabetized(step):
    assert_policy_entries(["a", "display_name", "z"], ['"zebra"', '"Robot Super Course"', '"apple"'])

def create_entry(key, value):
    css_click(".new-advanced-policy-item")
    newKey = css_find('#__new_advanced_key__ input').first
    newKey.fill(key)
#   For some reason have to get the instance for each command (get error that it is no longer attached to the DOM)
#   Have to do all this because Selenium has a bug that fill does not remove existing text
    css_find('.CodeMirror textarea').last.double_click()
    css_find('.CodeMirror textarea').last._element.send_keys(Keys.ARROW_LEFT)
    css_find('.CodeMirror textarea').last.fill(value)

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
    assert_equal(len(expected_values),len(webElements))
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