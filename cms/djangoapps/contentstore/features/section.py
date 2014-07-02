# pylint: disable=C0111
# pylint: disable=W0621

from lettuce import world, step
from common import *
from nose.tools import assert_equal  # pylint: disable=E0611


@step('I click the New Section link$')
def i_click_new_section_link(_step):
    link_css = 'a.new-courseware-section-button'
    world.css_click(link_css)


@step('I enter the section name and click save$')
def i_save_section_name(_step):
    save_section_name('My Section')


@step('I enter a section name with a quote and click save$')
def i_save_section_name_with_quote(_step):
    save_section_name('Section with "Quote"')


@step('I have added a new section$')
def i_have_added_new_section(_step):
    add_section()


@step('I click the Edit link for the release date$')
def i_click_the_edit_link_for_the_release_date(_step):
    button_css = 'div.section-published-date a.edit-release-date'
    world.css_click(button_css)


@step('I set the section release date to ([0-9/-]+)( [0-9:]+)?')
def set_section_release_date(_step, datestring, timestring):
    if hasattr(timestring, "strip"):
        timestring = timestring.strip()
    if not timestring:
        timestring = "00:00"
    set_date_and_time(
        'input.start-date.date.hasDatepicker', datestring,
        'input.start-time.time.ui-timepicker-input', timestring)
    world.browser.click_link_by_text('Save')


@step('I see a "(saving|deleting)" notification')
def i_see_a_mini_notification(_step, _type):
    saving_css = '.wrapper-notification-mini'
    assert world.is_css_present(saving_css)


@step('I see my section on the Courseware page$')
def i_see_my_section_on_the_courseware_page(_step):
    see_my_section_on_the_courseware_page('My Section')


@step('I see my section name with a quote on the Courseware page$')
def i_see_my_section_name_with_quote_on_the_courseware_page(_step):
    see_my_section_on_the_courseware_page('Section with "Quote"')


@step('I click to edit the section name$')
def i_click_to_edit_section_name(_step):
    world.css_click('span.section-name-span')


@step('I click on section name in Section Release Date modal$')
def i_click_on_section_name_in_modal(_step):
    world.css_click('.modal-window .section-name')


@step('I see no form for editing section name in modal$')
def edit_section_name_form_not_exist(_step):
    assert world.is_css_not_present('.modal-window .section-name input')


@step('I see the complete section name with a quote in the editor$')
def i_see_complete_section_name_with_quote_in_editor(_step):
    css = '.section-name-edit input[type=text]'
    assert world.is_css_present(css)
    assert_equal(world.css_value(css), 'Section with "Quote"')


@step('the section does not exist$')
def section_does_not_exist(_step):
    css = 'h3[data-name="My Section"]'
    assert world.is_css_not_present(css)


@step('I see a release date for my section$')
def i_see_a_release_date_for_my_section(_step):
    import re

    css = 'span.published-status'
    assert world.is_css_present(css)
    status_text = world.css_text(css)

    # e.g. 11/06/2012 at 16:25
    msg = 'Release date:'
    date_regex = r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) \d\d?, \d{4}'
    if not re.search(date_regex, status_text):
        print status_text, date_regex
    time_regex = r'[0-2]\d:[0-5]\d( \w{3})?'
    if not re.search(time_regex, status_text):
        print status_text, time_regex
    match_string = r'%s\s+%s at %s' % (msg, date_regex, time_regex)
    if not re.match(match_string, status_text):
        print status_text, match_string
    assert re.match(match_string, status_text)


@step('I see a link to create a new subsection$')
def i_see_a_link_to_create_a_new_subsection(_step):
    css = 'a.new-subsection-item'
    assert world.is_css_present(css)


@step('the section release date picker is not visible$')
def the_section_release_date_picker_not_visible(_step):
    css = 'div.edit-subsection-publish-settings'
    assert not world.css_visible(css)


@step('the section release date is updated$')
def the_section_release_date_is_updated(_step):
    css = 'span.published-status'
    status_text = world.css_text(css)
    assert_equal(status_text, 'Release date: 12/25/2013 at 00:00 UTC')


def save_section_name(name):
    name_css = '.new-section-name'
    save_css = '.new-section-name-save'
    world.css_fill(name_css, name)
    world.css_click(save_css)


def see_my_section_on_the_courseware_page(name):
    section_css = 'span.section-name-span'
    assert world.css_has_text(section_css, name)
