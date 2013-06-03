#pylint: disable=C0111
#pylint: disable=W0621

from lettuce import world, step
from common import *
from nose.tools import assert_equal

############### ACTIONS ####################


@step('I have opened a new course section in Studio$')
def i_have_opened_a_new_course_section(step):
    open_new_course()
    add_section()


@step('I have added a new subsection$')
def i_have_added_a_new_subsection(step):
    add_subsection()


@step('I have opened a new subsection in Studio$')
def i_have_opened_a_new_subsection(step):
    step.given('I have opened a new course section in Studio')
    step.given('I have added a new subsection')
    world.css_click('span.subsection-name-value')


@step('I click the New Subsection link')
def i_click_the_new_subsection_link(step):
    world.css_click('a.new-subsection-item')


@step('I enter the subsection name and click save$')
def i_save_subsection_name(step):
    save_subsection_name('Subsection One')


@step('I enter a subsection name with a quote and click save$')
def i_save_subsection_name_with_quote(step):
    save_subsection_name('Subsection With "Quote"')


@step('I click to edit the subsection name$')
def i_click_to_edit_subsection_name(step):
    world.css_click('span.subsection-name-value')


@step('I see the complete subsection name with a quote in the editor$')
def i_see_complete_subsection_name_with_quote_in_editor(step):
    css = '.subsection-display-name-input'
    assert world.is_css_present(css)
    assert_equal(world.css_find(css).value, 'Subsection With "Quote"')


@step('I have set a release date and due date in different years$')
def test_have_set_dates_in_different_years(step):
    set_date_and_time('input#start_date', '12/25/2011', 'input#start_time', '03:00')
    world.css_click('.set-date')
    # Use a year in the past so that current year will always be different.
    set_date_and_time('input#due_date', '01/02/2012', 'input#due_time', '04:00')


@step('I mark it as Homework$')
def i_mark_it_as_homework(step):
    world.css_click('a.menu-toggle')
    world.browser.click_link_by_text('Homework')


@step('I see it marked as Homework$')
def i_see_it_marked__as_homework(step):
    assert_equal(world.css_find(".status-label").value, 'Homework')


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


@step('I see the correct dates$')
def i_see_the_correct_dates(step):
    assert_equal('12/25/2011', get_date('input#start_date'))
    assert_equal('03:00', get_date('input#start_time'))
    assert_equal('01/02/2012', get_date('input#due_date'))
    assert_equal('04:00', get_date('input#due_time'))


############ HELPER METHODS ###################

def get_date(css):
    return world.css_find(css).first.value.strip()


def save_subsection_name(name):
    name_css = 'input.new-subsection-name-input'
    save_css = 'input.new-subsection-name-save'
    world.css_fill(name_css, name)
    world.css_click(save_css)


def see_subsection_name(name):
    css = 'span.subsection-name'
    assert world.is_css_present(css)
    css = 'span.subsection-name-value'
    assert world.css_has_text(css, name)
