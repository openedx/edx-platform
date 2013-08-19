#pylint: disable=C0111

from django.contrib.auth.models import User
from lettuce import world, step
from lettuce.django import django_url
from common import course_id

from student.models import CourseEnrollment


@step('I view the LTI and it is not rendered$')
def lti_is_not_rendered(_step):
    # lti div has no class rendered
    assert world.is_css_not_present('div.lti.rendered')

    # error is shown
    assert world.css_visible('.error_message')

    # iframe is not visible
    assert not world.css_visible('iframe')

    #inside iframe test content is not presented
    with world.browser.get_iframe('ltiLaunchFrame') as iframe:
        # iframe does not contain functions from terrain/ui_helpers.py
        assert iframe.is_element_not_present_by_css('.result', wait_time=5)


@step('I view the LTI and it is rendered$')
def lti_is_rendered(_step):
    # lti div has class rendered
    assert world.is_css_present('div.lti.rendered')

    # error is hidden
    assert not world.css_visible('.error_message')

    # iframe is visible
    assert world.css_visible('iframe')

    #inside iframe test content is presented
    with world.browser.get_iframe('ltiLaunchFrame') as iframe:
        # iframe does not contain functions from terrain/ui_helpers.py
        assert iframe.is_element_present_by_css('.result', wait_time=5)
        assert ("This is LTI tool. Success." == world.retry_on_exception(
            lambda: iframe.find_by_css('.result')[0].text,
            max_attempts=5
        ))


@step('I view the LTI but incorrect_signature warning is rendered$')
def incorrect_lti_is_rendered(_step):
    # lti div has class rendered
    assert world.is_css_present('div.lti.rendered')

    # error is hidden
    assert not world.css_visible('.error_message')

    # iframe is visible
    assert world.css_visible('iframe')

    #inside iframe test content is presented
    with world.browser.get_iframe('ltiLaunchFrame') as iframe:
        # iframe does not contain functions from terrain/ui_helpers.py
        assert iframe.is_element_present_by_css('.result', wait_time=5)
        assert ("Wrong LTI signature" == world.retry_on_exception(
            lambda: iframe.find_by_css('.result')[0].text,
            max_attempts=5
        ))


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


@step('the course has an LTI component filled with correct fields$')
def add_correct_lti_to_course(_step):
    category = 'lti'
    world.ItemFactory.create(
        # parent_location=section_location(course),
        parent_location=world.scenario_dict['SEQUENTIAL'].location,
        category=category,
        display_name='LTI',
        metadata={
            'lti_id': 'correct_lti_id',
            'launch_url': world.lti_server.oauth_settings['lti_base'] + world.lti_server.oauth_settings['lti_endpoint']
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


@step('the course has an LTI component with incorrect fields$')
def add_incorrect_lti_to_course(_step):
    category = 'lti'
    world.ItemFactory.create(
        parent_location=world.scenario_dict['SEQUENTIAL'].location,
        category=category,
        display_name='LTI',
        metadata={
            'lti_id': 'incorrect_lti_id',
            'lti_url': world.lti_server.oauth_settings['lti_base'] + world.lti_server.oauth_settings['lti_endpoint']
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
