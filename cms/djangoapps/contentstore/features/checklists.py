from lettuce import world, step
from common import *
from terrain.steps import reload_the_page

############### ACTIONS ####################
@step('I select Checklists from the Tools menu$')
def i_select_checklists(step):
    expand_icon_css = 'li.nav-course-tools i.icon-expand'
    if world.browser.is_element_present_by_css(expand_icon_css):
        css_click(expand_icon_css)
    link_css = 'li.nav-course-tools-checklists a'
    css_click(link_css)


@step('I see the four default edX checklists$')
def i_see_default_checklists(step):
    checklists = css_find('.checklist-title')
    assert_equal(4, len(checklists))
    assert_true(checklists[0].text.endswith('Getting Started With Studio'))
    assert_true(checklists[1].text.endswith('Draft a Rough Course Outline'))
    assert_true(checklists[2].text.endswith("Explore edX\'s Support Tools"))
    assert_true(checklists[3].text.endswith('Draft your Course Introduction'))


@step('I can select tasks in a checklist$')
def i_can_select_tasks(step):
    # Use the 2nd checklist as a reference
    assert_equal('0', css_find('#course-checklist1 .status-count').first.text)
    assert_equal('7', css_find('#course-checklist1 .status-amount').first.text)
    # TODO: check progress bar, select several items and check how things change


@step('They are still selected after I reload the page$')
def tasks_still_selected_after_reload(step):
    reload_the_page(step)
