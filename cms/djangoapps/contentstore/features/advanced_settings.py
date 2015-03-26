# pylint: disable=missing-docstring
# pylint: disable=redefined-outer-name

from lettuce import world, step
from nose.tools import assert_false, assert_equal, assert_regexp_matches  # pylint: disable=no-name-in-module
from common import type_in_codemirror, press_the_notification_button, get_codemirror_value

KEY_CSS = '.key h3.title'
DISPLAY_NAME_KEY = "Course Display Name"
DISPLAY_NAME_VALUE = '"Robot Super Course"'
ADVANCED_MODULES_KEY = "Advanced Module List"
# A few deprecated settings for testing toggling functionality.
DEPRECATED_SETTINGS = ["CSS Class for Course Reruns", "Hide Progress Tab", "XQA Key"]


@step('I select the Advanced Settings$')
def i_select_advanced_settings(step):

    world.click_course_settings()

    # The click handlers are set up so that if you click <body>
    # the menu disappears.  This means that if we're even a *little*
    # bit off on the last item ('Advanced Settings'), the menu
    # will close and the test will fail.
    # For this reason, we retrieve the link and visit it directly
    # This is what the browser *should* be doing, since it's just a native
    # link with no JavaScript involved.
    link_css = 'li.nav-course-settings-advanced a'
    world.wait_for_visible(link_css)
    link = world.css_find(link_css).first['href']
    world.visit(link)


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
        [ADVANCED_MODULES_KEY, DISPLAY_NAME_KEY, "Show Calculator"], ["[]", DISPLAY_NAME_VALUE, "false"])


@step('the settings are alphabetized$')
def they_are_alphabetized(step):
    key_elements = world.css_find(KEY_CSS)
    all_keys = []
    for key in key_elements:
        all_keys.append(key.value)

    assert_equal(sorted(all_keys), all_keys, "policy keys were not sorted")


@step('it is displayed as formatted$')
def it_is_formatted(step):
    assert_policy_entries(['Discussion Topic Mapping'], ['{\n    "key": "value",\n    "key_2": "value_2"\n}'])


@step('I get an error on save$')
def error_on_save(step):
    assert_regexp_matches(
        world.css_text('.error-item-message'),
        "Value stored in a .* must be .*, found .*"
    )


@step('it is displayed as a string')
def it_is_displayed_as_string(step):
    assert_policy_entries([DISPLAY_NAME_KEY], ['"quote me"'])


@step(u'the policy key value is unchanged$')
def the_policy_key_value_is_unchanged(step):
    assert_equal(get_display_name_value(), DISPLAY_NAME_VALUE)


@step(u'the policy key value is changed$')
def the_policy_key_value_is_changed(step):
    assert_equal(get_display_name_value(), '"foo"')


@step(u'deprecated settings are (then|not) shown$')
def verify_deprecated_settings_shown(_step, expected):
    for setting in DEPRECATED_SETTINGS:
        if expected == "not":
            assert_equal(-1, get_index_of(setting))
        else:
            world.wait_for(lambda _: get_index_of(setting) != -1)


@step(u'I toggle the display of deprecated settings$')
def toggle_deprecated_settings(_step):
    world.css_click(".deprecated-settings-label")


def assert_policy_entries(expected_keys, expected_values):
    for key, value in zip(expected_keys, expected_values):
        index = get_index_of(key)
        assert_false(index == -1, "Could not find key: {key}".format(key=key))
        found_value = get_codemirror_value(index)
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
    return get_codemirror_value(index)


def change_display_name_value(step, new_value):
    change_value(step, DISPLAY_NAME_KEY, new_value)


def change_value(step, key, new_value):
    index = get_index_of(key)
    type_in_codemirror(index, new_value)
    press_the_notification_button(step, "Save")
    world.wait_for_ajax_complete()
