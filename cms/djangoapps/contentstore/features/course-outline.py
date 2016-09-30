# pylint: disable=missing-docstring
# pylint: disable=redefined-outer-name

from lettuce import world, step
from common import *
from nose.tools import assert_true, assert_false

from logging import getLogger
logger = getLogger(__name__)


@step(u'I have a course with no sections$')
def have_a_course(step):
    world.clear_courses()
    course = world.CourseFactory.create()


@step(u'I have a course with 1 section$')
def have_a_course_with_1_section(step):
    world.clear_courses()
    course = world.CourseFactory.create()
    section = world.ItemFactory.create(parent_location=course.location)
    subsection1 = world.ItemFactory.create(
        parent_location=section.location,
        category='sequential',
        display_name='Subsection One',)


@step(u'I have a course with multiple sections$')
def have_a_course_with_two_sections(step):
    world.clear_courses()
    course = world.CourseFactory.create()
    section = world.ItemFactory.create(parent_location=course.location)
    subsection1 = world.ItemFactory.create(
        parent_location=section.location,
        category='sequential',
        display_name='Subsection One',)
    section2 = world.ItemFactory.create(
        parent_location=course.location,
        display_name='Section Two',)
    subsection2 = world.ItemFactory.create(
        parent_location=section2.location,
        category='sequential',
        display_name='Subsection Alpha',)
    subsection3 = world.ItemFactory.create(
        parent_location=section2.location,
        category='sequential',
        display_name='Subsection Beta',)


@step(u'I navigate to the course outline page$')
def navigate_to_the_course_outline_page(step):
    create_studio_user(is_staff=True)
    log_into_studio()
    course_locator = 'a.course-link'
    world.css_click(course_locator)


@step(u'I navigate to the outline page of a course with multiple sections')
def nav_to_the_outline_page_of_a_course_with_multiple_sections(step):
    step.given('I have a course with multiple sections')
    step.given('I navigate to the course outline page')


@step(u'I add a section')
def i_add_a_section(step):
    add_section()


@step(u'I press the section delete icon')
def i_press_the_section_delete_icon(step):
    delete_locator = 'section .outline-section > .section-header a.delete-button'
    world.css_click(delete_locator)


@step(u'I will confirm all alerts')
def i_confirm_all_alerts(step):
    confirm_locator = '.prompt .nav-actions button.action-primary'
    world.css_click(confirm_locator)


@step(u'I see the "([^"]*) All Sections" link$')
def i_see_the_collapse_expand_all_span(step, text):
    if text == "Collapse":
        span_locator = '.button-toggle-expand-collapse .collapse-all .label'
    elif text == "Expand":
        span_locator = '.button-toggle-expand-collapse .expand-all .label'
    assert_true(world.css_visible(span_locator))


@step(u'I do not see the "([^"]*) All Sections" link$')
def i_do_not_see_the_collapse_expand_all_span(step, text):
    if text == "Collapse":
        span_locator = '.button-toggle-expand-collapse .collapse-all .label'
    elif text == "Expand":
        span_locator = '.button-toggle-expand-collapse .expand-all .label'
    assert_false(world.css_visible(span_locator))


@step(u'I click the "([^"]*) All Sections" link$')
def i_click_the_collapse_expand_all_span(step, text):
    if text == "Collapse":
        span_locator = '.button-toggle-expand-collapse .collapse-all .label'
    elif text == "Expand":
        span_locator = '.button-toggle-expand-collapse .expand-all .label'
    assert_true(world.browser.is_element_present_by_css(span_locator))
    world.css_click(span_locator)


@step(u'I ([^"]*) the first section$')
def i_collapse_expand_a_section(step, text):
    if text == "collapse":
        locator = 'section .outline-section .ui-toggle-expansion'
    elif text == "expand":
        locator = 'section .outline-section .ui-toggle-expansion'
    world.css_click(locator)


@step(u'all sections are ([^"]*)$')
def all_sections_are_collapsed_or_expanded(step, text):
    subsection_locator = 'div.subsection-list'
    subsections = world.css_find(subsection_locator)
    for index in range(len(subsections)):
        if text == "collapsed":
            assert_false(world.css_visible(subsection_locator, index=index))
        elif text == "expanded":
            assert_true(world.css_visible(subsection_locator, index=index))


@step(u"I change an assignment's grading status")
def change_grading_status(step):
    world.css_find('a.menu-toggle').click()
    world.css_find('.menu li').first.click()
