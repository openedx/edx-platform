# disable missing docstring
#pylint: disable=C0111

from lettuce import world, step
from nose.tools import assert_equal
from common import type_in_codemirror

DISPLAY_NAME = "Display Name"
MAXIMUM_ATTEMPTS = "Maximum Attempts"
PROBLEM_WEIGHT = "Problem Weight"
RANDOMIZATION = 'Randomization'
SHOW_ANSWER = "Show Answer"


############### ACTIONS ####################
@step('I have created a Blank Common Problem$')
def i_created_blank_common_problem(step):
    world.create_component_instance(
        step,
        '.large-problem-icon',
        'i4x://edx/templates/problem/Blank_Common_Problem',
        '.xmodule_CapaModule'
    )


@step('I edit and select Settings$')
def i_edit_and_select_settings(step):
    world.edit_component_and_select_settings()


@step('I see five alphabetized settings and their expected values$')
def i_see_five_settings_with_values(step):
    world.verify_all_setting_entries(
        [
            [DISPLAY_NAME, "Blank Common Problem", True],
            [MAXIMUM_ATTEMPTS, "", False],
            [PROBLEM_WEIGHT, "", False],
            [RANDOMIZATION, "Never", True],
            [SHOW_ANSWER, "Finished", True]
        ])


@step('I can modify the display name')
def i_can_modify_the_display_name(step):
    # Verifying that the display name can be a string containing a floating point value
    # (to confirm that we don't throw an error because it is of the wrong type).
    world.get_setting_entry(DISPLAY_NAME).find_by_css('.setting-input')[0].fill('3.4')
    verify_modified_display_name()


@step('my display name change is persisted on save')
def my_display_name_change_is_persisted_on_save(step):
    world.save_component_and_reopen(step)
    verify_modified_display_name()


@step('I can specify special characters in the display name')
def i_can_modify_the_display_name_with_special_chars(step):
    world.get_setting_entry(DISPLAY_NAME).find_by_css('.setting-input')[0].fill("updated ' \" &")
    verify_modified_display_name_with_special_chars()


@step('my special characters and persisted on save')
def special_chars_persisted_on_save(step):
    world.save_component_and_reopen(step)
    verify_modified_display_name_with_special_chars()


@step('I can revert the display name to unset')
def can_revert_display_name_to_unset(step):
    world.revert_setting_entry(DISPLAY_NAME)
    verify_unset_display_name()


@step('my display name is unset on save')
def my_display_name_is_persisted_on_save(step):
    world.save_component_and_reopen(step)
    verify_unset_display_name()


@step('I can select Per Student for Randomization')
def i_can_select_per_student_for_randomization(step):
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
    world.verify_setting_entry(world.get_setting_entry(RANDOMIZATION), RANDOMIZATION, "Always", False)


@step('I can set the weight to "(.*)"?')
def i_can_set_weight(step, weight):
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


@step('if I set the max attempts to "(.*)", it displays initially as "(.*)", and is persisted as "(.*)"')
def set_the_max_attempts(step, max_attempts_set, max_attempts_displayed, max_attempts_persisted):
    world.get_setting_entry(MAXIMUM_ATTEMPTS).find_by_css('.setting-input')[0].fill(max_attempts_set)
    world.verify_setting_entry(world.get_setting_entry(MAXIMUM_ATTEMPTS), MAXIMUM_ATTEMPTS, max_attempts_displayed, True)
    world.save_component_and_reopen(step)
    world.verify_setting_entry(world.get_setting_entry(MAXIMUM_ATTEMPTS), MAXIMUM_ATTEMPTS, max_attempts_persisted, True)


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
    step.given("I see five alphabetized settings and their expected values")


@step('I have created a LaTeX Problem')
def create_latex_problem(step):
    world.click_new_component_button(step, '.large-problem-icon')
    # Go to advanced tab.
    world.css_click('#ui-id-2')
    world.click_component_from_menu("i4x://edx/templates/problem/Problem_Written_in_LaTeX", '.xmodule_CapaModule')


@step('I edit and compile the High Level Source')
def edit_latex_source(step):
    open_high_level_source()
    type_in_codemirror(1, "hi")
    world.css_click('.hls-compile')


@step('my change to the High Level Source is persisted')
def high_level_source_persisted(step):
    def verify_text(driver):
        return world.css_find('.problem').text == 'hi'

    world.wait_for(verify_text)


@step('I view the High Level Source I see my changes')
def high_level_source_in_editor(step):
    open_high_level_source()
    assert_equal('hi', world.css_find('.source-edit-box').value)


def verify_high_level_source_links(step, visible):
    assert_equal(visible, world.is_css_present('.launch-latex-compiler'))
    world.cancel_component(step)
    assert_equal(visible, world.is_css_present('.upload-button'))


def verify_modified_weight():
    world.verify_setting_entry(world.get_setting_entry(PROBLEM_WEIGHT), PROBLEM_WEIGHT, "3.5", True)


def verify_modified_randomization():
    world.verify_setting_entry(world.get_setting_entry(RANDOMIZATION), RANDOMIZATION, "Per Student", True)


def verify_modified_display_name():
    world.verify_setting_entry(world.get_setting_entry(DISPLAY_NAME), DISPLAY_NAME, '3.4', True)


def verify_modified_display_name_with_special_chars():
    world.verify_setting_entry(world.get_setting_entry(DISPLAY_NAME), DISPLAY_NAME, "updated ' \" &", True)


def verify_unset_display_name():
    world.verify_setting_entry(world.get_setting_entry(DISPLAY_NAME), DISPLAY_NAME, '', False)


def set_weight(weight):
    world.get_setting_entry(PROBLEM_WEIGHT).find_by_css('.setting-input')[0].fill(weight)


def open_high_level_source():
    world.css_click('a.edit-button')
    world.css_click('.launch-latex-compiler > a')
