# pylint: disable=missing-docstring
import datetime
import os
import pytz
from django.conf import settings
from mock import patch
from pytz import UTC
from splinter.exceptions import ElementDoesNotExist
from selenium.common.exceptions import NoAlertPresentException
from nose.tools import assert_true, assert_equal, assert_in, assert_is_none
from lettuce import world, step

from courseware.tests.factories import InstructorFactory, BetaTesterFactory
from courseware.access import has_access
from student.tests.factories import UserFactory

from common import visit_scenario_item

TEST_COURSE_NAME = "test_course_a"


@step('I view the LTI and error is shown$')
def lti_is_not_rendered(_step):
    # error is shown
    assert world.is_css_present('.error_message', wait_time=0)

    # iframe is not presented
    assert not world.is_css_present('iframe', wait_time=0)

    # link is not presented
    assert not world.is_css_present('.link_lti_new_window', wait_time=0)


def check_lti_iframe_content(text):
    # inside iframe test content is presented
    location = world.scenario_dict['LTI'].location.html_id()
    iframe_name = 'ltiFrame-' + location
    with world.browser.get_iframe(iframe_name) as iframe:
        # iframe does not contain functions from terrain/ui_helpers.py
        assert iframe.is_element_present_by_css('.result', wait_time=0)
        assert (text == world.retry_on_exception(
            lambda: iframe.find_by_css('.result')[0].text,
            max_attempts=5
        ))


@step('I view the LTI and it is rendered in (.*)$')
def lti_is_rendered(_step, rendered_in):
    if rendered_in.strip() == 'iframe':
        world.wait_for_present('iframe')
        assert world.is_css_present('iframe', wait_time=2)
        assert not world.is_css_present('.link_lti_new_window', wait_time=0)
        assert not world.is_css_present('.error_message', wait_time=0)

        # iframe is visible
        assert world.css_visible('iframe')
        check_lti_iframe_content("This is LTI tool. Success.")

    elif rendered_in.strip() == 'new page':
        assert not world.is_css_present('iframe', wait_time=2)
        assert world.is_css_present('.link_lti_new_window', wait_time=0)
        assert not world.is_css_present('.error_message', wait_time=0)
        click_and_check_lti_popup()
    else:  # incorrect rendered_in parameter
        assert False


@step('I view the permission alert$')
def view_lti_permission_alert(_step):
    assert not world.is_css_present('iframe', wait_time=2)
    assert world.is_css_present('.link_lti_new_window', wait_time=0)
    assert not world.is_css_present('.error_message', wait_time=0)
    world.css_find('.link_lti_new_window').first.click()
    alert = world.browser.get_alert()
    assert alert is not None
    assert len(world.browser.windows) == 1


def check_no_alert():
    """
    Make sure the alert has gone away.

    Note that the splinter documentation indicates that
    get_alert should return None if no alert is present,
    however that is not the case. Instead a
    NoAlertPresentException is raised.
    """
    try:
        assert_is_none(world.browser.get_alert())
    except NoAlertPresentException:
        pass


@step('I accept the permission alert and view the LTI$')
def accept_lti_permission_alert(_step):
    parent_window = world.browser.current_window  # Save the parent window

    # To start with you should only have one window/tab
    assert len(world.browser.windows) == 1
    alert = world.browser.get_alert()
    alert.accept()
    check_no_alert()

    # Give it a few seconds for the LTI window to appear
    world.wait_for(
        lambda _: len(world.browser.windows) == 2,
        timeout=5,
        timeout_msg="Timed out waiting for the LTI window to appear."
    )

    # Verify the LTI window
    check_lti_popup(parent_window)


@step('I reject the permission alert and do not view the LTI$')
def reject_lti_permission_alert(_step):
    alert = world.browser.get_alert()
    alert.dismiss()
    check_no_alert()
    assert len(world.browser.windows) == 1


@step('I view the LTI but incorrect_signature warning is rendered$')
def incorrect_lti_is_rendered(_step):
    assert world.is_css_present('iframe', wait_time=2)
    assert not world.is_css_present('.link_lti_new_window', wait_time=0)
    assert not world.is_css_present('.error_message', wait_time=0)

    # inside iframe test content is presented
    check_lti_iframe_content("Wrong LTI signature")


@step('the course has correct LTI credentials with registered (.*)$')
def set_correct_lti_passport(_step, user='Instructor'):
    coursenum = TEST_COURSE_NAME
    metadata = {
        'lti_passports': ["correct_lti_id:test_client_key:test_client_secret"]
    }

    i_am_registered_for_the_course(coursenum, metadata, user)


@step('the course has incorrect LTI credentials$')
def set_incorrect_lti_passport(_step):
    coursenum = TEST_COURSE_NAME
    metadata = {
        'lti_passports': ["test_lti_id:test_client_key:incorrect_lti_secret_key"]
    }

    i_am_registered_for_the_course(coursenum, metadata)


@step(r'the course has an LTI component with (.*) fields(?:\:)?$')  # , new_page is(.*), graded is(.*)
def add_correct_lti_to_course(_step, fields):
    category = 'lti'
    metadata = {
        'lti_id': 'correct_lti_id',
        'launch_url': 'http://127.0.0.1:{}/correct_lti_endpoint'.format(settings.LTI_PORT),
    }

    if fields.strip() == 'incorrect_lti_id':  # incorrect fields
        metadata.update({
            'lti_id': 'incorrect_lti_id'
        })
    elif fields.strip() == 'correct':  # correct fields
        pass
    elif fields.strip() == 'no_launch_url':
        metadata.update({
            'launch_url': u''
        })
    else:  # incorrect parameter
        assert False

    if _step.hashes:
        metadata.update(_step.hashes[0])

    world.scenario_dict['LTI'] = world.ItemFactory.create(
        parent_location=world.scenario_dict['SECTION'].location,
        category=category,
        display_name='LTI',
        metadata=metadata,
    )

    world.scenario_dict['LTI'].TEST_BASE_PATH = '{host}:{port}'.format(
        host=world.browser.host,
        port=world.browser.port,
    )

    visit_scenario_item('LTI')


def create_course_for_lti(course, metadata):
    # First clear the modulestore so we don't try to recreate
    # the same course twice
    # This also ensures that the necessary templates are loaded
    world.clear_courses()

    weight = 0.1
    grading_policy = {
        "GRADER": [
            {
                "type": "Homework",
                "min_count": 1,
                "drop_count": 0,
                "short_label": "HW",
                "weight": weight
            },
        ]
    }

    # Create the course
    # We always use the same org and display name,
    # but vary the course identifier (e.g. 600x or 191x)
    world.scenario_dict['COURSE'] = world.CourseFactory.create(
        org='edx',
        number=course,
        display_name='Test Course',
        metadata=metadata,
        grading_policy=grading_policy,
    )

    # Add a section to the course to contain problems
    world.scenario_dict['CHAPTER'] = world.ItemFactory.create(
        parent_location=world.scenario_dict['COURSE'].location,
        category='chapter',
        display_name='Test Chapter',
    )
    world.scenario_dict['SECTION'] = world.ItemFactory.create(
        parent_location=world.scenario_dict['CHAPTER'].location,
        category='sequential',
        display_name='Test Section',
        metadata={'graded': True, 'format': 'Homework'})


@patch.dict('courseware.access.settings.FEATURES', {'DISABLE_START_DATES': False})
def i_am_registered_for_the_course(coursenum, metadata, user='Instructor'):
    # Create user
    if user == 'BetaTester':
        # Create the course
        now = datetime.datetime.now(pytz.UTC)
        tomorrow = now + datetime.timedelta(days=5)
        metadata.update({'days_early_for_beta': 5, 'start': tomorrow})
        create_course_for_lti(coursenum, metadata)
        course_descriptor = world.scenario_dict['COURSE']

        # create beta tester
        user = BetaTesterFactory(course_key=course_descriptor.id)
        normal_student = UserFactory()
        instructor = InstructorFactory(course_key=course_descriptor.id)

        assert not has_access(normal_student, 'load', course_descriptor)
        assert has_access(user, 'load', course_descriptor)
        assert has_access(instructor, 'load', course_descriptor)
    else:
        metadata.update({'start': datetime.datetime(1970, 1, 1, tzinfo=UTC)})
        create_course_for_lti(coursenum, metadata)
        course_descriptor = world.scenario_dict['COURSE']
        user = InstructorFactory(course_key=course_descriptor.id)

    # Enroll the user in the course and log them in
    if has_access(user, 'load', course_descriptor):
        world.enroll_user(user, course_descriptor.id)

    world.log_in(username=user.username, password='test')


def check_lti_popup(parent_window):
    # You should now have 2 browser windows open, the original courseware and the LTI
    windows = world.browser.windows
    assert_equal(len(windows), 2)

    # For verification, iterate through the window titles and make sure that
    # both are there.
    tabs = []
    expected_tabs = [
        u'LTI | Test Section | {course} Courseware | {platform}'.format(
            course=TEST_COURSE_NAME,
            platform=settings.PLATFORM_NAME
        ),
        u'TEST TITLE'
    ]

    for window in windows:
        world.browser.switch_to_window(window)
        tabs.append(world.browser.title)
    assert_equal(tabs, expected_tabs)

    # Now verify the contents of the LTI window (which is the 2nd window/tab)
    # Note: The LTI opens in a new browser window, but Selenium sticks with the
    # current window until you explicitly switch to the context of the new one.
    world.browser.switch_to_window(windows[1])
    url = world.browser.url
    basename = os.path.basename(url)
    pathname = os.path.splitext(basename)[0]
    assert_equal(pathname, u'correct_lti_endpoint')

    result = world.css_find('.result').first.text
    assert_equal(result, u'This is LTI tool. Success.')

    world.browser.driver.close()  # Close the pop-up window
    world.browser.switch_to_window(parent_window)  # Switch to the main window again


def click_and_check_lti_popup():
    parent_window = world.browser.current_window  # Save the parent window
    world.css_find('.link_lti_new_window').first.click()
    check_lti_popup(parent_window)


@step('visit the LTI component')
def visit_lti_component(_step):
    visit_scenario_item('LTI')


@step('I see LTI component (.*) with text "([^"]*)"$')
def see_elem_text(_step, elem, text):
    selector_map = {
        'progress': '.problem-progress',
        'feedback': '.problem-feedback',
        'module title': '.problem-header',
        'button': '.link_lti_new_window',
        'description': '.lti-description'
    }
    assert_in(elem, selector_map)
    assert_true(world.css_has_text(selector_map[elem], text))


@step('I see text "([^"]*)"$')
def check_progress(_step, text):
    assert world.browser.is_text_present(text)


@step('I see graph with total progress "([^"]*)"$')
def see_graph(_step, progress):
    selector = 'grade-detail-graph'
    xpath = '//div[@id="{parent}"]//div[text()="{progress}"]'.format(
        parent=selector,
        progress=progress,
    )
    node = world.browser.find_by_xpath(xpath)
    assert node


@step('I see in the gradebook table that "([^"]*)" is "([^"]*)"$')
def see_value_in_the_gradebook(_step, label, text):
    table_selector = '.grade-table'
    index = 0
    table_headers = world.css_find('{0} thead th'.format(table_selector))

    for i, element in enumerate(table_headers):
        if element.text.strip() == label:
            index = i
            break

    assert_true(world.css_has_text('{0} tbody td'.format(table_selector), text, index=index))


@step('I submit answer to LTI (.*) question$')
def click_grade(_step, version):
    version_map = {
        '1': {'selector': 'submit-button', 'expected_text': 'LTI consumer (edX) responded with XML content'},
        '2': {'selector': 'submit-lti2-button', 'expected_text': 'LTI consumer (edX) responded with HTTP 200'},
    }
    assert_in(version, version_map)
    location = world.scenario_dict['LTI'].location.html_id()
    iframe_name = 'ltiFrame-' + location
    with world.browser.get_iframe(iframe_name) as iframe:
        iframe.find_by_name(version_map[version]['selector']).first.click()
        assert iframe.is_text_present(version_map[version]['expected_text'])


@step('LTI provider deletes my grade and feedback$')
def click_delete_button(_step):
    with world.browser.get_iframe(get_lti_frame_name()) as iframe:
        iframe.find_by_name('submit-lti2-delete-button').first.click()


def get_lti_frame_name():
    location = world.scenario_dict['LTI'].location.html_id()
    return 'ltiFrame-' + location


@step('I see in iframe that LTI role is (.*)$')
def check_role(_step, role):
    world.wait_for_present('iframe')
    location = world.scenario_dict['LTI'].location.html_id()
    iframe_name = 'ltiFrame-' + location
    with world.browser.get_iframe(iframe_name) as iframe:
        expected_role = 'Role: ' + role
        role = world.retry_on_exception(
            lambda: iframe.find_by_tag('h5').first.value,
            max_attempts=5,
            ignored_exceptions=ElementDoesNotExist
        )
        assert_equal(expected_role, role)


@step('I switch to (.*)$')
def switch_view(_step, view):
    staff_status = world.css_find('#action-preview-select').first.value
    if staff_status != view:
        world.browser.select("select", view)
        world.wait_for_ajax_complete()
        assert_equal(world.css_find('#action-preview-select').first.value, view)


@step("in the LTI component I do not see (.*)$")
def check_lti_component_no_elem(_step, text):
    selector_map = {
        'a launch button': '.link_lti_new_window',
        'an provider iframe': '.ltiLaunchFrame',
        'feedback': '.problem-feedback',
        'progress': '.problem-progress',
    }
    assert_in(text, selector_map)
    assert_true(world.is_css_not_present(selector_map[text]))
