from lettuce import world, step
from common import *
from nose.tools import assert_equal, assert_true

############### ACTIONS ####################


@step('I have opened a new course section in Studio$')
def i_have_opened_a_new_course_section(step):
    clear_courses()
    log_into_studio()
    create_a_course()
    add_section()


@step('I have added a new subsection$')
def i_have_added_a_new_subsection(step):
    add_subsection()


@step('I have opened a new subsection in Studio$')
def i_have_opened_a_new_subsection(step):
    step.given('I have opened a new course section in Studio')
    step.given('I have added a new subsection')
    css_click('span.subsection-name-value')


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


@step('I have set a release date and due date in different years$')
def test_have_set_dates_in_different_years(step):
    set_date_and_time('input#start_date', '12/25/2013', 'input#start_time', '3:00am')
    css_click('.set-date')
    set_date_and_time('input#due_date', '1/2/2014', 'input#due_time', '4:00am')


@step('I see the correct dates$')
def i_see_the_correct_dates(step):
    assert_equal('12/25/2013', css_find('input#start_date').first.value)
    assert_equal('3:00am', css_find('input#start_time').first.value)
    assert_equal('1/2/2014', css_find('input#due_date').first.value)
    assert_equal('4:00am', css_find('input#due_time').first.value)


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
