#pylint: disable=C0111
#pylint: disable=W0621

from lettuce import world, step
from terrain.steps import reload_the_page
from selenium.webdriver.common.keys import Keys
import time

from nose.tools import assert_true, assert_false, assert_equal

COURSE_START_DATE_CSS = "#course-start-date"
COURSE_END_DATE_CSS = "#course-end-date"
ENROLLMENT_START_DATE_CSS = "#course-enrollment-start-date"
ENROLLMENT_END_DATE_CSS = "#course-enrollment-end-date"

COURSE_START_TIME_CSS = "#course-start-time"
COURSE_END_TIME_CSS = "#course-end-time"
ENROLLMENT_START_TIME_CSS = "#course-enrollment-start-time"
ENROLLMENT_END_TIME_CSS = "#course-enrollment-end-time"

DUMMY_TIME = "15:30"
DEFAULT_TIME = "00:00"


############### ACTIONS ####################
@step('I select Schedule and Details$')
def test_i_select_schedule_and_details(step):
    world.click_course_settings()
    link_css = 'li.nav-course-settings-schedule a'
    world.css_click(link_css)


@step('I have set course dates$')
def test_i_have_set_course_dates(step):
    step.given('I have opened a new course in Studio')
    step.given('I select Schedule and Details')
    step.given('And I set course dates')


@step('And I set course dates$')
def test_and_i_set_course_dates(step):
    set_date_or_time(COURSE_START_DATE_CSS, '12/20/2013')
    set_date_or_time(COURSE_END_DATE_CSS, '12/26/2013')
    set_date_or_time(ENROLLMENT_START_DATE_CSS, '12/1/2013')
    set_date_or_time(ENROLLMENT_END_DATE_CSS, '12/10/2013')

    set_date_or_time(COURSE_START_TIME_CSS, DUMMY_TIME)
    set_date_or_time(ENROLLMENT_END_TIME_CSS, DUMMY_TIME)

    pause()


@step('Then I see the set dates on refresh$')
def test_then_i_see_the_set_dates_on_refresh(step):
    reload_the_page(step)
    verify_date_or_time(COURSE_START_DATE_CSS, '12/20/2013')
    verify_date_or_time(COURSE_END_DATE_CSS, '12/26/2013')
    verify_date_or_time(ENROLLMENT_START_DATE_CSS, '12/01/2013')
    verify_date_or_time(ENROLLMENT_END_DATE_CSS, '12/10/2013')

    verify_date_or_time(COURSE_START_TIME_CSS, DUMMY_TIME)
    # Unset times get set to 12 AM once the corresponding date has been set.
    verify_date_or_time(COURSE_END_TIME_CSS, DEFAULT_TIME)
    verify_date_or_time(ENROLLMENT_START_TIME_CSS, DEFAULT_TIME)
    verify_date_or_time(ENROLLMENT_END_TIME_CSS, DUMMY_TIME)


@step('And I clear all the dates except start$')
def test_and_i_clear_all_the_dates_except_start(step):
    set_date_or_time(COURSE_END_DATE_CSS, '')
    set_date_or_time(ENROLLMENT_START_DATE_CSS, '')
    set_date_or_time(ENROLLMENT_END_DATE_CSS, '')

    pause()


@step('Then I see cleared dates on refresh$')
def test_then_i_see_cleared_dates_on_refresh(step):
    reload_the_page(step)
    verify_date_or_time(COURSE_END_DATE_CSS, '')
    verify_date_or_time(ENROLLMENT_START_DATE_CSS, '')
    verify_date_or_time(ENROLLMENT_END_DATE_CSS, '')

    verify_date_or_time(COURSE_END_TIME_CSS, '')
    verify_date_or_time(ENROLLMENT_START_TIME_CSS, '')
    verify_date_or_time(ENROLLMENT_END_TIME_CSS, '')

    # Verify course start date (required) and time still there
    verify_date_or_time(COURSE_START_DATE_CSS, '12/20/2013')
    verify_date_or_time(COURSE_START_TIME_CSS, DUMMY_TIME)


@step('I clear the course start date$')
def test_i_clear_the_course_start_date(step):
    set_date_or_time(COURSE_START_DATE_CSS, '')


@step('I receive a warning about course start date$')
def test_i_receive_a_warning_about_course_start_date(step):
    assert_true(world.css_has_text('.message-error', 'The course must have an assigned start date.'))
    assert_true('error' in world.css_find(COURSE_START_DATE_CSS).first._element.get_attribute('class'))
    assert_true('error' in world.css_find(COURSE_START_TIME_CSS).first._element.get_attribute('class'))


@step('The previously set start date is shown on refresh$')
def test_the_previously_set_start_date_is_shown_on_refresh(step):
    reload_the_page(step)
    verify_date_or_time(COURSE_START_DATE_CSS, '12/20/2013')
    verify_date_or_time(COURSE_START_TIME_CSS, DUMMY_TIME)


@step('Given I have tried to clear the course start$')
def test_i_have_tried_to_clear_the_course_start(step):
    step.given("I have set course dates")
    step.given("I clear the course start date")
    step.given("I receive a warning about course start date")


@step('I have entered a new course start date$')
def test_i_have_entered_a_new_course_start_date(step):
    set_date_or_time(COURSE_START_DATE_CSS, '12/22/2013')
    pause()


@step('The warning about course start date goes away$')
def test_the_warning_about_course_start_date_goes_away(step):
    assert_equal(0, len(world.css_find('.message-error')))
    assert_false('error' in world.css_find(COURSE_START_DATE_CSS).first._element.get_attribute('class'))
    assert_false('error' in world.css_find(COURSE_START_TIME_CSS).first._element.get_attribute('class'))


@step('My new course start date is shown on refresh$')
def test_my_new_course_start_date_is_shown_on_refresh(step):
    reload_the_page(step)
    verify_date_or_time(COURSE_START_DATE_CSS, '12/22/2013')
    # Time should have stayed from before attempt to clear date.
    verify_date_or_time(COURSE_START_TIME_CSS, DUMMY_TIME)


############### HELPER METHODS ####################
def set_date_or_time(css, date_or_time):
    """
    Sets date or time field.
    """
    world.css_fill(css, date_or_time)
    e = world.css_find(css).first
    # hit Enter to apply the changes
    e._element.send_keys(Keys.ENTER)


def verify_date_or_time(css, date_or_time):
    """
    Verifies date or time field.
    """
    assert_equal(date_or_time, world.css_find(css).first.value)


def pause():
    """
    Must sleep briefly to allow last time save to finish,
    else refresh of browser will fail.
    """
    time.sleep(float(1))
