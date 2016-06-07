# disable missing docstring
# pylint: disable=missing-docstring

import json
from lettuce import world, step
from nose.tools import assert_equal, assert_true
from common import type_in_codemirror, open_new_course
from advanced_settings import change_value, ADVANCED_MODULES_KEY
from course_import import import_file

DISPLAY_NAME = "Display Name"
MAXIMUM_ATTEMPTS = "Maximum Attempts"
PROBLEM_WEIGHT = "Problem Weight"
RANDOMIZATION = 'Randomization'
SHOW_ANSWER = "Show Answer"
SHOW_RESET_BUTTON = "Show Reset Button"
TIMER_BETWEEN_ATTEMPTS = "Timer Between Attempts"
MATLAB_API_KEY = "Matlab API key"


@step('I have created a Blank Common Problem$')
def i_created_blank_common_problem(step):
    step.given('I am in Studio editing a new unit')
    step.given("I have created another Blank Common Problem")


@step('I have created a unit with advanced module "(.*)"$')
def i_created_unit_with_advanced_module(step, advanced_module):
    step.given('I am in Studio editing a new unit')

    url = world.browser.url
    step.given("I select the Advanced Settings")
    change_value(step, ADVANCED_MODULES_KEY, '["{}"]'.format(advanced_module))
    world.visit(url)
    world.wait_for_xmodule()


@step('I have created an advanced component "(.*)" of type "(.*)"')
def i_create_new_advanced_component(step, component_type, advanced_component):
    world.create_component_instance(
        step=step,
        category='advanced',
        component_type=component_type,
        advanced_component=advanced_component
    )


@step('I have created another Blank Common Problem$')
def i_create_new_common_problem(step):
    world.create_component_instance(
        step=step,
        category='problem',
        component_type='Blank Common Problem'
    )


@step('when I mouseover on "(.*)"')
def i_mouseover_on_html_component(step, element_class):
    action_css = '.{}'.format(element_class)
    world.trigger_event(action_css, event='mouseover')


@step(u'I can see Reply to Annotation link$')
def i_see_reply_to_annotation_link(_step):
    css_selector = 'a.annotatable-reply'
    world.wait_for_visible(css_selector)


@step(u'I see that page has scrolled "(.*)" when I click on "(.*)" link$')
def i_see_annotation_problem_page_scrolls(_step, scroll_direction, link_css):
    scroll_js = "$(window).scrollTop();"
    scroll_height_before = world.browser.evaluate_script(scroll_js)
    world.css_click("a.{}".format(link_css))
    scroll_height_after = world.browser.evaluate_script(scroll_js)
    if scroll_direction == "up":
        assert scroll_height_after < scroll_height_before
    elif scroll_direction == "down":
        assert scroll_height_after > scroll_height_before


@step('I have created an advanced problem of type "(.*)"$')
def i_create_new_advanced_problem(step, component_type):
    world.create_component_instance(
        step=step,
        category='problem',
        component_type=component_type,
        is_advanced=True
    )


@step('I edit and select Settings$')
def i_edit_and_select_settings(_step):
    world.edit_component_and_select_settings()


@step('I see the advanced settings and their expected values$')
def i_see_advanced_settings_with_values(step):
    world.verify_all_setting_entries(
        [
            [DISPLAY_NAME, "Blank Common Problem", True],
            [MATLAB_API_KEY, "", False],
            [MAXIMUM_ATTEMPTS, "", False],
            [PROBLEM_WEIGHT, "", False],
            [RANDOMIZATION, "Never", False],
            [SHOW_ANSWER, "Finished", False],
            [SHOW_RESET_BUTTON, "False", False],
            [TIMER_BETWEEN_ATTEMPTS, "0", False],
        ])


@step('I can modify the display name')
def i_can_modify_the_display_name(_step):
    # Verifying that the display name can be a string containing a floating point value
    # (to confirm that we don't throw an error because it is of the wrong type).
    index = world.get_setting_entry_index(DISPLAY_NAME)
    world.set_field_value(index, '3.4')
    verify_modified_display_name()


@step('my display name change is persisted on save')
def my_display_name_change_is_persisted_on_save(step):
    world.save_component_and_reopen(step)
    verify_modified_display_name()


@step('the problem display name is "(.*)"$')
def verify_problem_display_name(step, name):
    """
    name is uppercased because the heading styles are uppercase in css
    """
    assert_equal(name, world.browser.find_by_css('.problem-header').text)


@step('I can specify special characters in the display name')
def i_can_modify_the_display_name_with_special_chars(_step):
    index = world.get_setting_entry_index(DISPLAY_NAME)
    world.set_field_value(index, "updated ' \" &")
    verify_modified_display_name_with_special_chars()


@step('I can specify html in the display name and save')
def i_can_modify_the_display_name_with_html(_step):
    """
    If alert appear on save then UnexpectedAlertPresentException
    will occur and test will fail.
    """
    index = world.get_setting_entry_index(DISPLAY_NAME)
    world.set_field_value(index, "<script>alert('test')</script>")
    verify_modified_display_name_with_html()
    world.save_component()


@step('my special characters and persisted on save')
def special_chars_persisted_on_save(step):
    world.save_component_and_reopen(step)
    verify_modified_display_name_with_special_chars()


@step('I can revert the display name to unset')
def can_revert_display_name_to_unset(_step):
    world.revert_setting_entry(DISPLAY_NAME)
    verify_unset_display_name()


@step('my display name is unset on save')
def my_display_name_is_persisted_on_save(step):
    world.save_component_and_reopen(step)
    verify_unset_display_name()


@step('I can select Per Student for Randomization')
def i_can_select_per_student_for_randomization(_step):
    world.browser.select(RANDOMIZATION, "Per Student")
    verify_modified_randomization()


@step('my change to randomization is persisted')
def my_change_to_randomization_is_persisted(step):
    world.save_component_and_reopen(step)
    verify_modified_randomization()


@step('I can revert to the default value for randomization')
def i_can_revert_to_default_for_randomization(step):
    world.revert_setting_entry(RANDOMIZATION)
    world.save_component_and_reopen(step)
    world.verify_setting_entry(world.get_setting_entry(RANDOMIZATION), RANDOMIZATION, "Never", False)


@step('I can set the weight to "(.*)"?')
def i_can_set_weight(_step, weight):
    set_weight(weight)
    verify_modified_weight()


@step('my change to weight is persisted')
def my_change_to_weight_is_persisted(step):
    world.save_component_and_reopen(step)
    verify_modified_weight()


@step('I can revert to the default value of unset for weight')
def i_can_revert_to_default_for_unset_weight(step):
    world.revert_setting_entry(PROBLEM_WEIGHT)
    world.save_component_and_reopen(step)
    world.verify_setting_entry(world.get_setting_entry(PROBLEM_WEIGHT), PROBLEM_WEIGHT, "", False)


@step('if I set the weight to "(.*)", it remains unset')
def set_the_weight_to_abc(step, bad_weight):
    set_weight(bad_weight)
    # We show the clear button immediately on type, hence the "True" here.
    world.verify_setting_entry(world.get_setting_entry(PROBLEM_WEIGHT), PROBLEM_WEIGHT, "", True)
    world.save_component_and_reopen(step)
    # But no change was actually ever sent to the model, so on reopen, explicitly_set is False
    world.verify_setting_entry(world.get_setting_entry(PROBLEM_WEIGHT), PROBLEM_WEIGHT, "", False)


@step('if I set the max attempts to "(.*)", it will persist as a valid integer$')
def set_the_max_attempts(step, max_attempts_set):
    # on firefox with selenium, the behavior is different.
    # eg 2.34 displays as 2.34 and is persisted as 2
    index = world.get_setting_entry_index(MAXIMUM_ATTEMPTS)
    world.set_field_value(index, max_attempts_set)
    world.save_component_and_reopen(step)
    value = world.css_value('input.setting-input', index=index)
    assert value != "", "max attempts is blank"
    assert int(value) >= 0


@step('Edit High Level Source is not visible')
def edit_high_level_source_not_visible(step):
    verify_high_level_source_links(step, False)


@step('Edit High Level Source is visible')
def edit_high_level_source_links_visible(step):
    verify_high_level_source_links(step, True)


@step('If I press Cancel my changes are not persisted')
def cancel_does_not_save_changes(step):
    world.cancel_component(step)
    step.given("I edit and select Settings")
    step.given("I see the advanced settings and their expected values")


@step('I have enabled latex compiler')
def enable_latex_compiler(step):
    url = world.browser.url
    step.given("I select the Advanced Settings")
    change_value(step, 'Enable LaTeX Compiler', 'true')
    world.visit(url)
    world.wait_for_xmodule()


@step('I have created a LaTeX Problem')
def create_latex_problem(step):
    step.given('I am in Studio editing a new unit')
    step.given('I have enabled latex compiler')
    world.create_component_instance(
        step=step,
        category='problem',
        component_type='Problem Written in LaTeX',
        is_advanced=True
    )


@step('I edit and compile the High Level Source')
def edit_latex_source(_step):
    open_high_level_source()
    type_in_codemirror(1, "hi")
    world.css_click('.hls-compile')


@step('my change to the High Level Source is persisted')
def high_level_source_persisted(_step):
    def verify_text(driver):
        css_sel = '.problem div>span'
        return world.css_text(css_sel) == 'hi'

    world.wait_for(verify_text, timeout=10)


@step('I view the High Level Source I see my changes')
def high_level_source_in_editor(_step):
    open_high_level_source()
    assert_equal('hi', world.css_value('.source-edit-box'))


@step(u'I have an empty course')
def i_have_empty_course(step):
    open_new_course()


@step(u'I import the file "([^"]*)"$')
def i_import_the_file(_step, filename):
    import_file(filename)


@step(u'I go to the vertical "([^"]*)"$')
def i_go_to_vertical(_step, vertical):
    world.css_click("span:contains('{0}')".format(vertical))


@step(u'I go to the unit "([^"]*)"$')
def i_go_to_unit(_step, unit):
    loc = "window.location = $(\"span:contains('{0}')\").closest('a').attr('href')".format(unit)
    world.browser.execute_script(loc)


@step(u'I see a message that says "([^"]*)"$')
def i_can_see_message(_step, msg):
    msg = json.dumps(msg)     # escape quotes
    world.css_has_text("h2.title", msg)


@step(u'I can edit the problem$')
def i_can_edit_problem(_step):
    world.edit_component()


@step(u'I edit first blank advanced problem for annotation response$')
def i_edit_blank_problem_for_annotation_response(_step):
    world.edit_component(1)
    text = """
        <problem>
            <annotationresponse>
                <annotationinput><text>Text of annotation</text></annotationinput>
            </annotationresponse>
        </problem>"""
    type_in_codemirror(0, text)
    world.save_component()


@step(u'I can see cheatsheet$')
def verify_cheat_sheet_displaying(_step):
    world.css_click(".cheatsheet-toggle")
    css_selector = '.simple-editor-cheatsheet'
    world.wait_for_visible(css_selector)


def verify_high_level_source_links(step, visible):
    if visible:
        assert_true(world.is_css_present('.launch-latex-compiler'),
                    msg="Expected to find the latex button but it is not present.")
    else:
        assert_true(world.is_css_not_present('.launch-latex-compiler'),
                    msg="Expected not to find the latex button but it is present.")

    world.cancel_component(step)


def verify_modified_weight():
    world.verify_setting_entry(world.get_setting_entry(PROBLEM_WEIGHT), PROBLEM_WEIGHT, "3.5", True)


def verify_modified_randomization():
    world.verify_setting_entry(world.get_setting_entry(RANDOMIZATION), RANDOMIZATION, "Per Student", True)


def verify_modified_display_name():
    world.verify_setting_entry(world.get_setting_entry(DISPLAY_NAME), DISPLAY_NAME, '3.4', True)


def verify_modified_display_name_with_special_chars():
    world.verify_setting_entry(world.get_setting_entry(DISPLAY_NAME), DISPLAY_NAME, "updated ' \" &", True)


def verify_modified_display_name_with_html():
    world.verify_setting_entry(world.get_setting_entry(DISPLAY_NAME), DISPLAY_NAME, "<script>alert('test')</script>", True)


def verify_unset_display_name():
    world.verify_setting_entry(world.get_setting_entry(DISPLAY_NAME), DISPLAY_NAME, 'Blank Advanced Problem', False)


def set_weight(weight):
    index = world.get_setting_entry_index(PROBLEM_WEIGHT)
    world.set_field_value(index, weight)


def open_high_level_source():
    world.edit_component()
    world.css_click('.launch-latex-compiler > a')
