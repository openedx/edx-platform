# pylint: disable=C0111
# pylint: disable=W0621

from lettuce import world, step
from common import *

############### ACTIONS ####################


@step('There are no courses$')
def no_courses(step):
    world.clear_courses()
    create_studio_user()


@step('I click the New Course button$')
def i_click_new_course(step):
    world.css_click('.new-course-button')


@step('I fill in the new course information$')
def i_fill_in_a_new_course_information(step):
    fill_in_course_info()


@step('I create a course with "([^"]*)", "([^"]*)", "([^"]*)", and "([^"]*)"')
def i_create_course(step, name, org, number, run):
    fill_in_course_info(name=name, org=org, num=number, run=run)


@step('I create a new course$')
def i_create_a_course(step):
    create_a_course()


@step('I click the course link in My Courses$')
def i_click_the_course_link_in_my_courses(step):
    course_css = 'a.course-link'
    world.css_click(course_css)


@step('I see an error about the length of the org/course/run tuple')
def i_see_error_about_length(step):
    assert world.css_has_text('#course_creation_error', 'The combined length of the organization, course number, and course run fields cannot be more than 65 characters.')

############ ASSERTIONS ###################


@step('the Courseware page has loaded in Studio$')
def courseware_page_has_loaded_in_studio(step):
    course_title_css = 'span.course-title'
    assert world.is_css_present(course_title_css)


@step('I see the course listed in My Courses$')
def i_see_the_course_in_my_courses(step):
    course_css = 'h3.class-title'
    assert world.css_has_text(course_css, world.scenario_dict['COURSE'].display_name)


@step('I am on the "([^"]*)" tab$')
def i_am_on_tab(step, tab_name):
    header_css = 'div.inner-wrapper h1'
    assert world.css_has_text(header_css, tab_name)


@step('I see a link for adding a new section$')
def i_see_new_section_link(step):
    link_css = '.outline .button-new'
    assert world.css_has_text(link_css, 'New Section')
