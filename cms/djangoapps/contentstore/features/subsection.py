# pylint: disable=C0111
# pylint: disable=W0621

from lettuce import world, step
from common import *
from nose.tools import assert_equal  # pylint: disable=E0611

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
    world.css_click('.outline-item-section .add-button')


@step('I enter the subsection name and click save$')
def i_save_subsection_name(step):
    save_subsection_name('Subsection One')


@step('I enter a subsection name with a quote and click save$')
def i_save_subsection_name_with_quote(step):
    save_subsection_name('Subsection With "Quote"')


@step('I click on the subsection$')
def click_on_subsection(step):
    world.css_click('span.subsection-name-value')


@step('I see the complete subsection name with a quote in the editor$')
def i_see_complete_subsection_name_with_quote_in_editor(step):
    css = '.subsection-display-name-input'
    assert world.is_css_present(css)
    assert_equal(world.css_value(css), 'Subsection With "Quote"')


@step('I set the subsection release date to ([0-9/-]+)( [0-9:]+)?')
def set_subsection_release_date(_step, datestring, timestring):
    set_subsection_date('input#start_date', datestring, 'input#start_time', timestring)


@step('I set the subsection release date on enter to ([0-9/-]+)( [0-9:]+)?')
def set_subsection_release_date_on_enter(_step, datestring, timestring):  # pylint: disable-msg=invalid-name
    set_subsection_date('input#start_date', datestring, 'input#start_time', timestring, 'ENTER')


@step('I set the subsection due date to ([0-9/-]+)( [0-9:]+)?')
def set_subsection_due_date(_step, datestring, timestring, key=None):
    if not world.css_visible('input#due_date'):
        world.css_click('.due-date-input .set-date')

    assert world.css_visible('input#due_date')
    set_subsection_date('input#due_date', datestring, 'input#due_time', timestring, key)


@step('I set the subsection due date on enter to ([0-9/-]+)( [0-9:]+)?')
def set_subsection_due_date_on_enter(_step, datestring, timestring):  # pylint: disable-msg=invalid-name
    set_subsection_due_date(_step, datestring, timestring, 'ENTER')


@step('I mark it as Homework$')
def i_mark_it_as_homework(step):
    world.css_click('a.menu-toggle')
    world.browser.click_link_by_text('Homework')


@step('I see it marked as Homework$')
def i_see_it_marked__as_homework(step):
    assert_equal(world.css_value(".status-label"), 'Homework')


@step('I click the link to sync release date to section')
def click_sync_release_date(step):
    world.css_click('.sync-date')


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
    assert world.is_css_not_present(css)


@step('I see the subsection release date is ([0-9/-]+)( [0-9:]+)?')
def i_see_subsection_release(_step, datestring, timestring):
    if hasattr(timestring, "strip"):
        timestring = timestring.strip()
    assert_equal(datestring, get_date('input#start_date'))
    if timestring:
        assert_equal(timestring, get_date('input#start_time'))


@step('I see the subsection due date is ([0-9/-]+)( [0-9:]+)?')
def i_see_subsection_due(_step, datestring, timestring):
    if hasattr(timestring, "strip"):
        timestring = timestring.strip()
    assert_equal(datestring, get_date('input#due_date'))
    if timestring:
        assert_equal(timestring, get_date('input#due_time'))


############ HELPER METHODS ###################
def get_date(css):
    return world.css_find(css).first.value.strip()


def save_subsection_name(name):
    name_css = 'input.new-subsection-name-input'
    save_css = 'input.new-subsection-name-save'
    world.css_fill(name_css, name)
    world.css_click(save_css)
    set_element_value('.xblock-field-input', name, Keys.ENTER)


def see_subsection_name(name):
    css = 'span.subsection-name'
    assert world.is_css_present(css)
    css = 'span.subsection-name-value'
    assert world.css_has_text(css, name)


def set_subsection_date(date_css, datestring, time_css, timestring, key=None):
    if hasattr(timestring, "strip"):
        timestring = timestring.strip()
    if not timestring:
        timestring = "00:00"

    set_date_and_time(date_css, datestring, time_css, timestring, key)
