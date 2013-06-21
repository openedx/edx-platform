#pylint: disable=C0111
#pylint: disable=W0621

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


@step('I create a new course$')
def i_create_a_course(step):
    create_a_course()


@step('I click the course link in My Courses$')
def i_click_the_course_link_in_my_courses(step):
    course_css = 'span.class-name'
    world.css_click(course_css)

############ ASSERTIONS ###################


@step('the Courseware page has loaded in Studio$')
def courseware_page_has_loaded_in_studio(step):
    course_title_css = 'span.course-title'
    assert world.is_css_present(course_title_css)


@step('I see the course listed in My Courses$')
def i_see_the_course_in_my_courses(step):
    course_css = 'span.class-name'
    assert world.css_has_text(course_css, 'Robot Super Course')


@step('I am on the "([^"]*)" tab$')
def i_am_on_tab(step, tab_name):
    header_css = 'div.inner-wrapper h1'
    assert world.css_has_text(header_css, tab_name)


@step('I see a link for adding a new section$')
def i_see_new_section_link(step):
    link_css = 'a.new-courseware-section-button'
    assert world.css_has_text(link_css, 'New Section')
