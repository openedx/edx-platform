from lettuce import world, step
from common import *
import time
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support import expected_conditions as EC

from nose.tools import assert_true, assert_false, assert_equal

"""
http://selenium.googlecode.com/svn/trunk/docs/api/py/webdriver/selenium.webdriver.common.keys.html
"""
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


# TODO: this is copied from terrain's step.py. Need to figure out how to share that code.
@step('I reload the page$')
def reload_the_page(step):
    world.browser.reload()


@step(u'I press the "([^"]*)" notification button$')
def press_the_notification_button(step, name):
    def is_visible(driver):
        return EC.visibility_of_element_located((By.CSS_SELECTOR,css,))
    def is_invisible(driver):
        return EC.invisibility_of_element_located((By.CSS_SELECTOR,css,))

    css = 'a.%s-button' % name.lower()
    wait_for(is_visible)

    try:
        css_click_at(css)
        wait_for(is_invisible)
    except WebDriverException, e:
        css_click_at(css)
        wait_for(is_invisible)

    if name == "Save":
        css = ""
        wait_for(is_visible)


@step(u'I edit the value of a policy key$')
def edit_the_value_of_a_policy_key(step):
    """
    It is hard to figure out how to get into the CodeMirror
    area, so cheat and do it from the policy key field :)
    """
    policy_key_css = 'input.policy-key'
    index = get_index_of("display_name")
    e = css_find(policy_key_css)[index]
    e._element.send_keys(Keys.TAB, Keys.END, Keys.ARROW_LEFT, ' ', 'X')


@step('I create a JSON object$')
def create_JSON_object(step):
    create_entry("json", '{"key": "value", "key_2": "value_2"}')
    click_save()


############### RESULTS ####################
@step('I see default advanced settings$')
def i_see_default_advanced_settings(step):
    # Test only a few of the existing properties (there are around 34 of them)
    assert_policy_entries(
        ["advanced_modules", "display_name", "show_calculator"], ["[]", '"Robot Super Course"', "false"], False)


@step('they are alphabetized$')
def they_are_alphabetized(step):
    assert_policy_entries(["a", "display_name", "z"], ['"zebra"', '"Robot Super Course"', '"apple"'])


@step('it is displayed as formatted$')
def it_is_formatted(step):
    assert_policy_entries(["display_name", "json"], ['"Robot Super Course"', '{\n    "key": "value",\n    "key_2": "value_2"\n}'])

@step(u'the policy key value is unchanged$')
def the_policy_key_value_is_unchanged(step):
    assert_equal(get_display_name_value(), '"Robot Super Course"')


@step(u'the policy key value is changed$')
def the_policy_key_value_is_changed(step):
    assert_equal(get_display_name_value(), '"Robot Super Course X"')


############# HELPERS ###############
def assert_policy_entries(expected_keys, expected_values, assertLength=True):
    key_css = '.key input.policy-key'
    key_elements = css_find(key_css)
    if assertLength:
        assert_equal(len(expected_keys), len(key_elements))

    value_css = 'textarea.json'
    for counter in range(len(expected_keys)):
        index = get_index_of(expected_keys[counter])
        assert_false(index == -1, "Could not find key: " + expected_keys[counter])
        assert_equal(expected_values[counter], css_find(value_css)[index].value, "value is incorrect")


def get_index_of(expected_key):
    key_css = '.key input.policy-key'
    for counter in range(len(css_find(key_css))):
        #   Sometimes get stale reference if I hold on to the array of elements
        key = css_find(key_css)[counter].value
        if key == expected_key:
            return counter

    return -1


def click_save():
    css = "a.save-button"
    css_click_at(css)


def get_display_name_value():
    policy_value_css = 'textarea.json'
    index = get_index_of("display_name")
    return css_find(policy_value_css)[index].value
