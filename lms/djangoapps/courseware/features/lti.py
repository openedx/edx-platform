#pylint: disable=C0111

from lettuce import world, step
from lettuce.django import django_url
from common import i_am_registered_for_the_course, section_location


@step('I view the LTI and it is not rendered')
def lti_is_not_rendered(_step):
    # lti div has no class rendered
    assert world.is_css_not_present('div.lti.rendered')

    # error is shown
    assert world.css_visible('.error_message')

    # iframe is not visible
    assert (not world.css_visible('iframe'))

    #inside iframe test content is not presented
    with world.browser.get_iframe('ltiLaunchFrame') as iframe:
        # iframe does not contain functions from terrain/ui_helpers.py
        assert iframe.is_element_not_present_by_css('.result', wait_time=5)


@step('I view the LTI and it is rendered')
def lti_is_rendered(_step):
    # lti div has class rendered
    assert world.is_css_present('div.lti.rendered')

    # error is hidden
    assert (not world.css_visible('.error_message'))

    # iframe is visible
    assert world.css_visible('iframe')

    #inside iframe test content is presented
    with world.browser.get_iframe('ltiLaunchFrame') as iframe:
        # iframe does not contain functions from terrain/ui_helpers.py
        assert iframe.is_element_present_by_css('.result', wait_time=5)


@step('the course has a LTI component filled with correct data')
def view_lti_with_data(_step):
    coursenum = 'test_course'
    i_am_registered_for_the_course(_step, coursenum)

    add_correct_lti_to_course(coursenum)
    chapter_name = world.scenario_dict['SECTION'].display_name.replace(
        " ", "_")
    section_name = chapter_name
    url = django_url('/courses/%s/%s/%s/courseware/%s/%s' % (
        world.scenario_dict['COURSE'].org,
        world.scenario_dict['COURSE'].number,
        world.scenario_dict['COURSE'].display_name.replace(' ', '_'),
        chapter_name, section_name,)
    )
    world.browser.visit(url)


@step('the course has a LTI component with empty fields')
def view_default_lti(_step):
    coursenum = 'test_course'
    i_am_registered_for_the_course(_step, coursenum)

    add_default_lti_to_course(coursenum)
    chapter_name = world.scenario_dict['SECTION'].display_name.replace(
        " ", "_")
    section_name = chapter_name
    url = django_url('/courses/%s/%s/%s/courseware/%s/%s' % (
        world.scenario_dict['COURSE'].org,
        world.scenario_dict['COURSE'].number,
        world.scenario_dict['COURSE'].display_name.replace(' ', '_'),
        chapter_name, section_name,)
    )
    world.browser.visit(url)


def add_correct_lti_to_course(course):
    category = 'lti'
    world.ItemFactory.create(
        parent_location=section_location(course),
        category=category,
        display_name='LTI',
        metadata={
            'client_key': 'client_key',
            'clent_secret': 'client_secret',
            'lti_url': 'http://127.0.0.1:{}/correct_lti_endpoint'.format(world.lti_server_port)
        }
    )


def add_default_lti_to_course(course):
    category = 'lti'
    world.ItemFactory.create(
        parent_location=section_location(course),
        category=category,
        display_name='LTI'
    )
