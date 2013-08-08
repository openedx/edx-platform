# pylint: disable=C0111
# pylint: disable=W0621

from lettuce import world, step
from common import *
from nose.tools import assert_true, assert_false, assert_equal  # pylint: disable=E0611

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


@step(u'I navigate to the course overview page$')
def navigate_to_the_course_overview_page(step):
    create_studio_user(is_staff=True)
    log_into_studio()
    course_locator = 'a.course-link'
    world.css_click(course_locator)


@step(u'I navigate to the courseware page of a course with multiple sections')
def nav_to_the_courseware_page_of_a_course_with_multiple_sections(step):
    step.given('I have a course with multiple sections')
    step.given('I navigate to the course overview page')


@step(u'I add a section')
def i_add_a_section(step):
    add_section(name='My New Section That I Just Added')


@step(u'I click the "([^"]*)" link$')
def i_click_the_text_span(step, text):
    span_locator = '.toggle-button-sections span'
    assert_true(world.browser.is_element_present_by_css(span_locator))
    # first make sure that the expand/collapse text is the one you expected
    assert_equal(world.browser.find_by_css(span_locator).value, text)
    world.css_click(span_locator)


@step(u'I collapse the first section$')
def i_collapse_a_section(step):
    collapse_locator = 'section.courseware-section a.collapse'
    world.css_click(collapse_locator)


@step(u'I expand the first section$')
def i_expand_a_section(step):
    expand_locator = 'section.courseware-section a.expand'
    world.css_click(expand_locator)


@step(u'I see the "([^"]*)" link$')
def i_see_the_span_with_text(step, text):
    span_locator = '.toggle-button-sections span'
    assert_true(world.is_css_present(span_locator))
    assert_equal(world.css_value(span_locator), text)
    assert_true(world.css_visible(span_locator))


@step(u'I do not see the "([^"]*)" link$')
def i_do_not_see_the_span_with_text(step, text):
    # Note that the span will exist on the page but not be visible
    span_locator = '.toggle-button-sections span'
    assert_true(world.is_css_present(span_locator))
    assert_false(world.css_visible(span_locator))


@step(u'all sections are expanded$')
def all_sections_are_expanded(step):
    subsection_locator = 'div.subsection-list'
    subsections = world.css_find(subsection_locator)
    for index in range(len(subsections)):
        assert_true(world.css_visible(subsection_locator, index=index))


@step(u'all sections are collapsed$')
def all_sections_are_collapsed(step):
    subsection_locator = 'div.subsection-list'
    subsections = world.css_find(subsection_locator)
    for index in range(len(subsections)):
        assert_false(world.css_visible(subsection_locator, index=index))


@step(u"I change an assignment's grading status")
def change_grading_status(step):
    world.css_find('a.menu-toggle').click()
    world.css_find('.menu li').first.click()


@step(u'I reorder subsections')
def reorder_subsections(_step):
    draggable_css = '.subsection-drag-handle'
    ele = world.css_find(draggable_css).first
    ele.action_chains.drag_and_drop_by_offset(
        ele._element,
        0,
        10
    ).perform()
