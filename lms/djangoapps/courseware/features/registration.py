# pylint: disable=missing-docstring

from lettuce import world, step
from lettuce.django import django_url
import time


@step('I register for the course "([^"]*)"$')
def i_register_for_the_course(_step, course):
    url = django_url('courses/%s/about' % world.scenario_dict['COURSE'].id.to_deprecated_string())
    world.browser.visit(url)
    world.css_click('.intro a.register')
    assert world.is_css_present('.container.dashboard')


@step('I register to audit the course$')
def i_register_to_audit_the_course(_step):
    url = django_url('courses/%s/about' % world.scenario_dict['COURSE'].id.to_deprecated_string())
    world.browser.visit(url)
    world.css_click('.intro a.register')
    # When the page first loads some animation needs to
    # complete before this button is in a stable location
    world.retry_on_exception(
        lambda: world.browser.find_by_name("honor_mode").click(),
        max_attempts=10,
        ignored_exceptions=AttributeError
    )
    time.sleep(1)
    assert world.is_css_present('.container.dashboard')


@step(u'I should see an empty dashboard message')
def i_should_see_empty_dashboard(_step):
    empty_dash_css = '.empty-dashboard-message'
    assert world.is_css_present(empty_dash_css)


@step(u'I should( NOT)? see the course numbered "([^"]*)" in my dashboard$')
def i_should_see_that_course_in_my_dashboard(_step, doesnt_appear, course):
    course_link_css = '.my-courses a[href*="%s"]' % course
    if doesnt_appear:
        assert world.is_css_not_present(course_link_css)
    else:
        assert world.is_css_present(course_link_css)


@step(u'I unenroll from the course numbered "([^"]*)"')
def i_unenroll_from_that_course(_step, course):
    more_actions_dropdown_link_selector = '[id*=actions-dropdown-link-0]'
    assert world.is_css_present(more_actions_dropdown_link_selector)
    world.css_click(more_actions_dropdown_link_selector)

    unregister_css = 'li.actions-item a.action-unenroll[data-course-number*="{course_number}"][href*=unenroll-modal]'.format(course_number=course)
    assert world.is_css_present(unregister_css)
    world.css_click(unregister_css)

    button_css = '#unenroll-modal input[value="Unenroll"]'
    assert world.is_css_present(button_css)
    world.css_click(button_css)
