# pylint: disable=C0111
# pylint: disable=W0621

from lettuce import world, step
from terrain.steps import reload_the_page
from selenium.webdriver.common.keys import Keys
from common import type_in_codemirror, upload_file
from django.conf import settings

from nose.tools import assert_true, assert_false, assert_equal  # pylint: disable=E0611

TEST_ROOT = settings.COMMON_TEST_DATA_ROOT

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
    world.wait_for_requirejs(
        ["jquery", "js/models/course",
         "js/models/settings/course_details", "js/views/settings/main"])


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


@step('And I clear all the dates except start$')
def test_and_i_clear_all_the_dates_except_start(step):
    set_date_or_time(COURSE_END_DATE_CSS, '')
    set_date_or_time(ENROLLMENT_START_DATE_CSS, '')
    set_date_or_time(ENROLLMENT_END_DATE_CSS, '')


@step('Then I see cleared dates$')
def test_then_i_see_cleared_dates(step):
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


@step('the previously set start date is shown$')
def test_the_previously_set_start_date_is_shown(step):
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


@step('The warning about course start date goes away$')
def test_the_warning_about_course_start_date_goes_away(step):
    assert world.is_css_not_present('.message-error')
    assert_false('error' in world.css_find(COURSE_START_DATE_CSS).first._element.get_attribute('class'))
    assert_false('error' in world.css_find(COURSE_START_TIME_CSS).first._element.get_attribute('class'))


@step('my new course start date is shown$')
def new_course_start_date_is_shown(step):
    verify_date_or_time(COURSE_START_DATE_CSS, '12/22/2013')
    # Time should have stayed from before attempt to clear date.
    verify_date_or_time(COURSE_START_TIME_CSS, DUMMY_TIME)


@step('I change fields$')
def test_i_change_fields(step):
    set_date_or_time(COURSE_START_DATE_CSS, '7/7/7777')
    set_date_or_time(COURSE_END_DATE_CSS, '7/7/7777')
    set_date_or_time(ENROLLMENT_START_DATE_CSS, '7/7/7777')
    set_date_or_time(ENROLLMENT_END_DATE_CSS, '7/7/7777')


@step('I change the course overview')
def test_change_course_overview(_step):
    type_in_codemirror(0, "<h1>Overview</h1>")


@step('I click the "Upload Course Image" button')
def click_upload_button(_step):
    button_css = '.action-upload-image'
    world.css_click(button_css)


@step('I upload a new course image$')
def upload_new_course_image(_step):
    upload_file('image.jpg', sub_path="uploads")


@step('I should see the new course image$')
def i_see_new_course_image(_step):
    img_css = '#course-image'
    images = world.css_find(img_css)
    assert len(images) == 1
    img = images[0]
    expected_src = '/c4x/MITx/999/asset/image.jpg'

    # Don't worry about the domain in the URL
    success_func = lambda _: img['src'].endswith(expected_src)
    world.wait_for(success_func)


@step('the image URL should be present in the field')
def image_url_present(_step):
    field_css = '#course-image-url'
    expected_value = '/c4x/MITx/999/asset/image.jpg'
    assert world.css_value(field_css) == expected_value


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
    # We need to wait for JavaScript to fill in the field, so we use
    # css_has_value(), which first checks that the field is not blank
    assert_true(world.css_has_value(css, date_or_time))


@step('I do not see the changes')
@step('I see the set dates')
def i_see_the_set_dates(_step):
    """
    Ensure that each field has the value set in `test_and_i_set_course_dates`.
    """
    verify_date_or_time(COURSE_START_DATE_CSS, '12/20/2013')
    verify_date_or_time(COURSE_END_DATE_CSS, '12/26/2013')
    verify_date_or_time(ENROLLMENT_START_DATE_CSS, '12/01/2013')
    verify_date_or_time(ENROLLMENT_END_DATE_CSS, '12/10/2013')

    verify_date_or_time(COURSE_START_TIME_CSS, DUMMY_TIME)
    # Unset times get set to 12 AM once the corresponding date has been set.
    verify_date_or_time(COURSE_END_TIME_CSS, DEFAULT_TIME)
    verify_date_or_time(ENROLLMENT_START_TIME_CSS, DEFAULT_TIME)
    verify_date_or_time(ENROLLMENT_END_TIME_CSS, DUMMY_TIME)
