#pylint: disable=C0111
#pylint: disable=W0621

from lettuce import world, step
from lettuce.django import django_url
from common import TEST_COURSE_ORG, TEST_COURSE_NAME


@step('I register for the course "([^"]*)"$')
def i_register_for_the_course(step, course):
    cleaned_name = TEST_COURSE_NAME.replace(' ', '_')
    url = django_url('courses/%s/%s/%s/about' % (TEST_COURSE_ORG, course, cleaned_name))
    world.browser.visit(url)

    intro_section = world.browser.find_by_css('section.intro')
    register_link = intro_section.find_by_css('a.register')
    register_link.click()

    assert world.is_css_present('section.container.dashboard')


@step(u'I should see the course numbered "([^"]*)" in my dashboard$')
def i_should_see_that_course_in_my_dashboard(step, course):
    course_link_css = 'section.my-courses a[href*="%s"]' % course
    assert world.is_css_present(course_link_css)


@step(u'I press the "([^"]*)" button in the Unenroll dialog')
def i_press_the_button_in_the_unenroll_dialog(step, value):
    button_css = 'section#unenroll-modal input[value="%s"]' % value
    world.css_click(button_css)
    assert world.is_css_present('section.container.dashboard')
