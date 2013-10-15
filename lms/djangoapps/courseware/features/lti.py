#pylint: disable=C0111

import os
from django.contrib.auth.models import User
from lettuce import world, step
from lettuce.django import django_url
from common import course_id

from student.models import CourseEnrollment


@step('I view the LTI and error is shown$')
def lti_is_not_rendered(_step):
    # error is shown
    assert world.is_css_present('.error_message')

    # iframe is not presented
    assert not world.is_css_present('iframe')

    # link is not presented
    assert not world.is_css_present('.link_lti_new_window')


def check_lti_iframe_content(text):
    #inside iframe test content is presented
    location = world.scenario_dict['LTI'].location.html_id()
    iframe_name = 'ltiLaunchFrame-' + location
    with world.browser.get_iframe(iframe_name) as iframe:
        # iframe does not contain functions from terrain/ui_helpers.py
        assert iframe.is_element_present_by_css('.result', wait_time=5)
        assert (text == world.retry_on_exception(
            lambda: iframe.find_by_css('.result')[0].text,
            max_attempts=5
        ))


@step('I view the LTI and it is rendered in (.*)$')
def lti_is_rendered(_step, rendered_in):
    if rendered_in.strip() == 'iframe':
        assert world.is_css_present('iframe')
        assert not world.is_css_present('.link_lti_new_window')
        assert not world.is_css_present('.error_message')

        # iframe is visible
        assert world.css_visible('iframe')
        check_lti_iframe_content("This is LTI tool. Success.")

    elif rendered_in.strip() == 'new page':
        assert not world.is_css_present('iframe')
        assert world.is_css_present('.link_lti_new_window')
        assert not world.is_css_present('.error_message')
        check_lti_popup()
    else:  # incorrent rendered_in parameter
        assert False


@step('I view the LTI but incorrect_signature warning is rendered$')
def incorrect_lti_is_rendered(_step):
    assert world.is_css_present('iframe')
    assert not world.is_css_present('.link_lti_new_window')
    assert not world.is_css_present('.error_message')
    #inside iframe test content is presented
    check_lti_iframe_content("Wrong LTI signature")


@step('the course has correct LTI credentials$')
def set_correct_lti_passport(_step):
    coursenum = 'test_course'
    metadata = {
        'lti_passports': ["correct_lti_id:{}:{}".format(
            world.lti_server.oauth_settings['client_key'],
            world.lti_server.oauth_settings['client_secret']
        )]
    }
    i_am_registered_for_the_course(coursenum, metadata)


@step('the course has incorrect LTI credentials$')
def set_incorrect_lti_passport(_step):
    coursenum = 'test_course'
    metadata = {
        'lti_passports': ["test_lti_id:{}:{}".format(
            world.lti_server.oauth_settings['client_key'],
            "incorrect_lti_secret_key"
        )]
    }
    i_am_registered_for_the_course(coursenum, metadata)


@step('the course has an LTI component with (.*) fields, new_page is(.*)$')
def add_correct_lti_to_course(_step, fields, new_page):
    category = 'lti'
    lti_id = 'correct_lti_id'
    launch_url = world.lti_server.oauth_settings['lti_base'] + world.lti_server.oauth_settings['lti_endpoint']
    if fields.strip() == 'incorrect_lti_id':  # incorrect fields
        lti_id = 'incorrect_lti_id'
    elif fields.strip() == 'correct':  # correct fields
        pass
    elif fields.strip() == 'no_launch_url':
        launch_url = u''
    else:  # incorrect parameter
        assert False

    if new_page.strip().lower() == 'false':
        new_page = False
    else:  # default is True
        new_page = True

    world.scenario_dict['LTI'] = world.ItemFactory.create(
        parent_location=world.scenario_dict['SEQUENTIAL'].location,
        category=category,
        display_name='LTI',
        metadata={
            'lti_id': lti_id,
            'launch_url': launch_url,
            'open_in_a_new_page': new_page
        }
    )
    course = world.scenario_dict["COURSE"]
    chapter_name = world.scenario_dict['SECTION'].display_name.replace(
        " ", "_")
    section_name = chapter_name
    path = "/courses/{org}/{num}/{name}/courseware/{chapter}/{section}".format(
        org=course.org,
        num=course.number,
        name=course.display_name.replace(' ', '_'),
        chapter=chapter_name,
        section=section_name)
    url = django_url(path)

    world.browser.visit(url)


def create_course(course, metadata):

    # First clear the modulestore so we don't try to recreate
    # the same course twice
    # This also ensures that the necessary templates are loaded
    world.clear_courses()

    # Create the course
    # We always use the same org and display name,
    # but vary the course identifier (e.g. 600x or 191x)
    world.scenario_dict['COURSE'] = world.CourseFactory.create(
        org='edx',
        number=course,
        display_name='Test Course',
        metadata=metadata
    )

    # Add a section to the course to contain problems
    world.scenario_dict['SECTION'] = world.ItemFactory.create(
        parent_location=world.scenario_dict['COURSE'].location,
        display_name='Test Section'
    )
    world.scenario_dict['SEQUENTIAL'] = world.ItemFactory.create(
        parent_location=world.scenario_dict['SECTION'].location,
        category='sequential',
        display_name='Test Section')


def i_am_registered_for_the_course(course, metadata):
    # Create the course
    create_course(course, metadata)

    # Create the user
    world.create_user('robot', 'test')
    usr = User.objects.get(username='robot')

    # If the user is not already enrolled, enroll the user.
    CourseEnrollment.enroll(usr, course_id(course))

    world.log_in(username='robot', password='test')


def check_lti_popup():
    parent_window = world.browser.current_window # Save the parent window
    world.css_find('.link_lti_new_window').first.click()

    assert len(world.browser.windows) != 1

    for window in world.browser.windows:
        world.browser.switch_to_window(window) # Switch to a different window (the pop-up)
        # Check if this is the one we want by comparing the url
        url = world.browser.url
        basename = os.path.basename(url)
        pathname = os.path.splitext(basename)[0]

        if pathname == u'correct_lti_endpoint':
            break

    result = world.css_find('.result').first.text
    assert result == u'This is LTI tool. Success.'

    world.browser.driver.close() # Close the pop-up window
    world.browser.switch_to_window(parent_window) # Switch to the main window again


