# pylint: disable=missing-docstring
# pylint: disable=redefined-outer-name

from lettuce import world, step
from nose.tools import assert_true, assert_equal
from selenium.common.exceptions import StaleElementReferenceException


############### ACTIONS ####################
@step('I select Checklists from the Tools menu$')
def i_select_checklists(step):
    world.click_tools()
    link_css = 'li.nav-course-tools-checklists a'
    world.css_click(link_css)
    world.wait_for_ajax_complete()


@step('I have opened Checklists$')
def i_have_opened_checklists(step):
    step.given('I have opened a new course in Studio')
    step.given('I select Checklists from the Tools menu')


@step('I see the four default edX checklists$')
def i_see_default_checklists(step):
    checklists = world.css_find('.checklist-title')
    assert_equal(4, len(checklists))
    assert_true(checklists[0].text.endswith('Getting Started With Studio'))
    assert_true(checklists[1].text.endswith('Draft a Rough Course Outline'))
    assert_true(checklists[2].text.endswith("Explore edX\'s Support Tools"))
    assert_true(checklists[3].text.endswith('Draft Your Course About Page'))


@step('I can check and uncheck tasks in a checklist$')
def i_can_check_and_uncheck_tasks(step):
    # Use the 2nd checklist as a reference
    verifyChecklist2Status(0, 7, 0)
    toggleTask(1, 0)
    verifyChecklist2Status(1, 7, 14)
    toggleTask(1, 3)
    verifyChecklist2Status(2, 7, 29)
    toggleTask(1, 6)
    verifyChecklist2Status(3, 7, 43)
    toggleTask(1, 3)
    verifyChecklist2Status(2, 7, 29)


@step('the tasks are correctly selected$')
def tasks_correctly_selected(step):
    verifyChecklist2Status(2, 7, 29)
    # verify that task 7 is still selected by toggling its checkbox state and making sure that it deselects
    world.browser.execute_script("window.scrollBy(0,1000)")
    toggleTask(1, 6)
    verifyChecklist2Status(1, 7, 14)


@step('I select a link to the course outline$')
def i_select_a_link_to_the_course_outline(step):
    clickActionLink(1, 0, 'Edit Course Outline')


@step('I am brought to the course outline page$')
def i_am_brought_to_course_outline(step):
    assert world.is_css_present('body.view-outline')
    assert_equal(1, len(world.browser.windows))


@step('I am brought back to the course outline in the correct state$')
def i_am_brought_back_to_course_outline(step):
    step.given('I see the four default edX checklists')
    # In a previous step, we selected (1, 0) in order to click the 'Edit Course Outline' link.
    # Make sure the task is still showing as selected (there was a caching bug with the collection).
    verifyChecklist2Status(1, 7, 14)


@step('I select a link to help page$')
def i_select_a_link_to_the_help_page(step):
    clickActionLink(2, 0, 'Visit Studio Help')


@step('I am brought to the help page in a new window$')
def i_am_brought_to_help_page_in_new_window(step):
    step.given('I see the four default edX checklists')
    windows = world.browser.windows
    assert_equal(2, len(windows))
    world.browser.switch_to_window(windows[1])
    assert_equal('http://help.edge.edx.org/', world.browser.url)


############### HELPER METHODS ####################
def verifyChecklist2Status(completed, total, percentage):
    def verify_count(driver):
        try:
            statusCount = world.css_find('#course-checklist1 .status-count').first
            return statusCount.text == str(completed)
        except StaleElementReferenceException:
            return False

    world.wait_for(verify_count)
    assert_equal(str(total), world.css_find('#course-checklist1 .status-amount').first.text)
    # Would like to check the CSS width, but not sure how to do that.
    assert_equal(str(percentage), world.css_find('#course-checklist1 .viz-checklist-status-value .int').first.text)


def toggleTask(checklist, task):
    world.css_click('#course-checklist' + str(checklist) + '-task' + str(task))
    world.wait_for_ajax_complete()


# TODO: figure out a way to do this in phantom and firefox
# For now we will mark the scenerios that use this method as skipped
def clickActionLink(checklist, task, actionText):
    # text will be empty initially, wait for it to populate
    def verify_action_link_text(driver):
        actualText = world.css_text('#course-checklist' + str(checklist) + ' a', index=task)
        if actualText == actionText:
            return True
        else:
            # toggle checklist item to make sure that the link button is showing
            toggleTask(checklist, task)
            return False

    world.wait_for(verify_action_link_text)
    world.css_click('#course-checklist' + str(checklist) + ' a', index=task)
    world.wait_for_ajax_complete()
