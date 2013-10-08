#pylint: disable=C0111
#pylint: disable=W0621

from lettuce import world, step
from nose.tools import assert_false, assert_equal, assert_regexp_matches  # pylint: disable=E0611
from common import type_in_codemirror, press_the_notification_button

KEY_CSS = '.key input.policy-key'
VALUE_CSS = 'textarea.json'
DISPLAY_NAME_KEY = "display_name"
DISPLAY_NAME_VALUE = '"Robot Super Course"'


@step('I select the Advanced Settings$')
def i_select_advanced_settings(step):
    world.click_course_settings()
    link_css = 'li.nav-course-settings-advanced a'
    world.css_click(link_css)
    world.wait_for_requirejs(
        ["jquery", "js/models/course", "js/models/settings/advanced",
         "js/views/settings/advanced", "codemirror"])
    # this shouldn't be necessary, but we experience sporadic failures otherwise
    world.wait(1)


@step('I am on the Advanced Course Settings page in Studio$')
def i_am_on_advanced_course_settings(step):
    step.given('I have opened a new course in Studio')
    step.given('I select the Advanced Settings')


@step(u'I edit the value of a policy key$')
def edit_the_value_of_a_policy_key(step):
    type_in_codemirror(get_index_of(DISPLAY_NAME_KEY), 'X')


@step(u'I edit the value of a policy key and save$')
def edit_the_value_of_a_policy_key_and_save(step):
    change_display_name_value(step, '"foo"')


@step('I create a JSON object as a value for "(.*)"$')
def create_JSON_object(step, key):
    change_value(step, key, '{"key": "value", "key_2": "value_2"}')


@step('I create a non-JSON value not in quotes$')
def create_value_not_in_quotes(step):
    change_display_name_value(step, 'quote me')


@step('I see default advanced settings$')
def i_see_default_advanced_settings(step):
    # Test only a few of the existing properties (there are around 34 of them)
    assert_policy_entries(
        ["advanced_modules", DISPLAY_NAME_KEY, "show_calculator"], ["[]", DISPLAY_NAME_VALUE, "false"])


@step('the settings are alphabetized$')
def they_are_alphabetized(step):
    key_elements = world.css_find(KEY_CSS)
    all_keys = []
    for key in key_elements:
        all_keys.append(key.value)

    assert_equal(sorted(all_keys), all_keys, "policy keys were not sorted")


@step('it is displayed as formatted$')
def it_is_formatted(step):
    assert_policy_entries(['discussion_topics'], ['{\n    "key": "value",\n    "key_2": "value_2"\n}'])


@step('I get an error on save$')
def error_on_save(step):
    assert_regexp_matches(world.css_text('#notification-error-description'), 'Incorrect setting format')


@step('it is displayed as a string')
def it_is_displayed_as_string(step):
    assert_policy_entries([DISPLAY_NAME_KEY], ['"quote me"'])


@step(u'the policy key value is unchanged$')
def the_policy_key_value_is_unchanged(step):
    assert_equal(get_display_name_value(), DISPLAY_NAME_VALUE)


@step(u'the policy key value is changed$')
def the_policy_key_value_is_changed(step):
    assert_equal(get_display_name_value(), '"foo"')


def assert_policy_entries(expected_keys, expected_values):
    for key, value in zip(expected_keys, expected_values):
        index = get_index_of(key)
        assert_false(index == -1, "Could not find key: {key}".format(key=key))
        found_value = world.css_find(VALUE_CSS)[index].value
        assert_equal(
            value, found_value,
            "Expected {} to have value {} but found {}".format(key, value, found_value)
        )


def get_index_of(expected_key):
    for i, element in enumerate(world.css_find(KEY_CSS)):
        # Sometimes get stale reference if I hold on to the array of elements
        key = world.css_value(KEY_CSS, index=i)
        if key == expected_key:
            return i

    return -1


def get_display_name_value():
    index = get_index_of(DISPLAY_NAME_KEY)
    return world.css_value(VALUE_CSS, index=index)


def change_display_name_value(step, new_value):
    change_value(step, DISPLAY_NAME_KEY, new_value)


def change_value(step, key, new_value):
    type_in_codemirror(get_index_of(key), new_value)
    world.wait(0.5)
    press_the_notification_button(step, "Save")
    world.wait_for_ajax_complete()
