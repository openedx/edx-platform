from lettuce import world, step
from common import *
from nose.tools import assert_equal

############### ACTIONS ####################


@step('I click the new section link$')
def i_click_new_section_link(step):
    link_css = 'a.new-courseware-section-button'
    css_click(link_css)


@step('I enter the section name and click save$')
def i_save_section_name(step):
    save_section_name('My Section')


@step('I enter a section name with a quote and click save$')
def i_save_section_name_with_quote(step):
    save_section_name('Section with "Quote"')


@step('I have added a new section$')
def i_have_added_new_section(step):
    add_section()


@step('I click the Edit link for the release date$')
def i_click_the_edit_link_for_the_release_date(step):
    button_css = 'div.section-published-date a.edit-button'
    css_click(button_css)


@step('I save a new section release date$')
def i_save_a_new_section_release_date(step):
    date_css = 'input.start-date.date.hasDatepicker'
    time_css = 'input.start-time.time.ui-timepicker-input'
    css_fill(date_css, '12/25/2013')
    # click here to make the calendar go away
    css_click(time_css)
    css_fill(time_css, '12:00am')
    css_click('a.save-button')


############ ASSERTIONS ###################


@step('I see my section on the Courseware page$')
def i_see_my_section_on_the_courseware_page(step):
    see_my_section_on_the_courseware_page('My Section')


@step('I see my section name with a quote on the Courseware page$')
def i_see_my_section_name_with_quote_on_the_courseware_page(step):
    see_my_section_on_the_courseware_page('Section with "Quote"')


@step('I click to edit the section name$')
def i_click_to_edit_section_name(step):
    css_click('span.section-name-span')


@step('I see the complete section name with a quote in the editor$')
def i_see_complete_section_name_with_quote_in_editor(step):
    css = '.edit-section-name'
    assert world.browser.is_element_present_by_css(css, 5)
    assert_equal(world.browser.find_by_css(css).value, 'Section with "Quote"')


@step('the section does not exist$')
def section_does_not_exist(step):
    css = 'span.section-name-span'
    assert world.browser.is_element_not_present_by_css(css)


@step('I see a release date for my section$')
def i_see_a_release_date_for_my_section(step):
    import re

    css = 'span.published-status'
    assert world.browser.is_element_present_by_css(css)
    status_text = world.browser.find_by_css(css).text

    # e.g. 11/06/2012 at 16:25
    msg = 'Will Release:'
    date_regex = '[01][0-9]\/[0-3][0-9]\/[12][0-9][0-9][0-9]'
    time_regex = '[0-2][0-9]:[0-5][0-9]'
    match_string = '%s %s at %s' % (msg, date_regex, time_regex)
    assert re.match(match_string, status_text)


@step('I see a link to create a new subsection$')
def i_see_a_link_to_create_a_new_subsection(step):
    css = 'a.new-subsection-item'
    assert world.browser.is_element_present_by_css(css)


@step('the section release date picker is not visible$')
def the_section_release_date_picker_not_visible(step):
    css = 'div.edit-subsection-publish-settings'
    assert False, world.browser.find_by_css(css).visible


@step('the section release date is updated$')
def the_section_release_date_is_updated(step):
    css = 'span.published-status'
    status_text = world.browser.find_by_css(css).text
    assert status_text == 'Will Release: 12/25/2013 at 12:00am'


############ HELPER METHODS ###################

def save_section_name(name):
    name_css = '.new-section-name'
    save_css = '.new-section-name-save'
    css_fill(name_css, name)
    css_click(save_css)


def see_my_section_on_the_courseware_page(name):
    section_css = 'span.section-name-span'
    assert_css_with_text(section_css, name)