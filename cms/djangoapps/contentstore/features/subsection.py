from lettuce import world, step
from common import *
from nose.tools import assert_equal

############### ACTIONS ####################


@step('I have opened a new course section in Studio$')
def i_have_opened_a_new_course_section(step):
    clear_courses()
    log_into_studio()
    create_a_course()
    add_section()


@step('I click the New Subsection link')
def i_click_the_new_subsection_link(step):
    css = 'a.new-subsection-item'
    css_click(css)


@step('I enter the subsection name and click save$')
def i_save_subsection_name(step):
    save_subsection_name('Subsection One')


@step('I enter a subsection name with a quote and click save$')
def i_save_subsection_name_with_quote(step):
    save_subsection_name('Subsection With "Quote"')


@step('I click to edit the subsection name$')
def i_click_to_edit_subsection_name(step):
    css_click('span.subsection-name-value')


@step('I see the complete subsection name with a quote in the editor$')
def i_see_complete_subsection_name_with_quote_in_editor(step):
    css = '.subsection-display-name-input'
    assert world.browser.is_element_present_by_css(css, 5)
    assert_equal(world.browser.find_by_css(css).value, 'Subsection With "Quote"')


@step('I have added a new subsection$')
def i_have_added_a_new_subsection(step):
    add_subsection()


############ ASSERTIONS ###################


@step('I see my subsection on the Courseware page$')
def i_see_my_subsection_on_the_courseware_page(step):
    see_subsection_name('Subsection One')


@step('I see my subsection name with a quote on the Courseware page$')
def i_see_my_subsection_name_with_quote_on_the_courseware_page(step):
    see_subsection_name('Subsection With "Quote"')


@step('the subsection does not exist$')
def the_subsection_does_not_exist(step):
    css = 'span.subsection-name'
    assert world.browser.is_element_not_present_by_css(css)


############ HELPER METHODS ###################

def save_subsection_name(name):
    name_css = 'input.new-subsection-name-input'
    save_css = 'input.new-subsection-name-save'
    css_fill(name_css, name)
    css_click(save_css)

def see_subsection_name(name):
    css = 'span.subsection-name'
    assert world.browser.is_element_present_by_css(css)
    css = 'span.subsection-name-value'
    assert_css_with_text(css, name)
