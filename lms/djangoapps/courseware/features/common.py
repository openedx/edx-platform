from lettuce import world, step
from django.core.management import call_command
from nose.tools import assert_equals, assert_in
from lettuce.django import django_url
from django.conf import settings
from django.contrib.auth.models import User
from student.models import CourseEnrollment
from terrain.factories import CourseFactory, ItemFactory
from xmodule.modulestore import Location
from xmodule.modulestore.django import _MODULESTORES, modulestore
from xmodule.templates import update_templates
import time

from logging import getLogger
logger = getLogger(__name__)


@step(u'I wait (?:for )?"(\d+)" seconds?$')
def wait(step, seconds):
    time.sleep(float(seconds))


@step('I (?:visit|access|open) the homepage$')
def i_visit_the_homepage(step):
    world.browser.visit(django_url('/'))
    assert world.browser.is_element_present_by_css('header.global', 10)


@step(u'I (?:visit|access|open) the dashboard$')
def i_visit_the_dashboard(step):
    world.browser.visit(django_url('/dashboard'))
    assert world.browser.is_element_present_by_css('section.container.dashboard', 5)


@step(r'click (?:the|a) link (?:called|with the text) "([^"]*)"$')
def click_the_link_called(step, text):
    world.browser.find_link_by_text(text).click()


@step('I should be on the dashboard page$')
def i_should_be_on_the_dashboard(step):
    assert world.browser.is_element_present_by_css('section.container.dashboard', 5)
    assert world.browser.title == 'Dashboard'


@step(u'I (?:visit|access|open) the courses page$')
def i_am_on_the_courses_page(step):
    world.browser.visit(django_url('/courses'))
    assert world.browser.is_element_present_by_css('section.courses')


@step('I should see that the path is "([^"]*)"$')
def i_should_see_that_the_path_is(step, path):
    assert world.browser.url == django_url(path)


@step(u'the page title should be "([^"]*)"$')
def the_page_title_should_be(step, title):
    assert world.browser.title == title


@step(r'should see that the url is "([^"]*)"$')
def should_have_the_url(step, url):
    assert_equals(world.browser.url, url)


@step(r'should see (?:the|a) link (?:called|with the text) "([^"]*)"$')
def should_see_a_link_called(step, text):
    assert len(world.browser.find_link_by_text(text)) > 0


@step(r'should see "(.*)" (?:somewhere|anywhere) in (?:the|this) page')
def should_see_in_the_page(step, text):
    assert_in(text, world.browser.html)


@step('I am logged in$')
def i_am_logged_in(step):
    world.create_user('robot')
    world.log_in('robot@edx.org', 'test')


@step('I am not logged in$')
def i_am_not_logged_in(step):
    world.browser.cookies.delete()


TEST_COURSE_ORG = 'edx'
TEST_COURSE_NAME = 'Test Course'
TEST_SECTION_NAME = "Problem"

@step(u'The course "([^"]*)" exists$')
def create_course(step, course):

    # First clear the modulestore so we don't try to recreate
    # the same course twice
    # This also ensures that the necessary templates are loaded
    flush_xmodule_store()

    # Create the course
    # We always use the same org and display name,
    # but vary the course identifier (e.g. 600x or 191x)
    course = CourseFactory.create(org=TEST_COURSE_ORG, 
                                number=course,
                                display_name=TEST_COURSE_NAME)

    # Add a section to the course to contain problems
    section = ItemFactory.create(parent_location=course.location,
                                display_name=TEST_SECTION_NAME)

    problem_section = ItemFactory.create(parent_location=section.location,
                                        template='i4x://edx/templates/sequential/Empty',
                                        display_name=TEST_SECTION_NAME)

@step(u'I am registered for the course "([^"]*)"$')
def i_am_registered_for_the_course(step, course):
    # Create the course
    create_course(step, course)

    # Create the user
    world.create_user('robot')
    u = User.objects.get(username='robot')

    # If the user is not already enrolled, enroll the user.
    CourseEnrollment.objects.get_or_create(user=u, course_id=course_id(course))

    world.log_in('robot@edx.org', 'test')

@step(u'The course "([^"]*)" has extra tab "([^"]*)"$')
def add_tab_to_course(step, course, extra_tab_name):
    section_item = ItemFactory.create(parent_location=course_location(course),
                                    template="i4x://edx/templates/static_tab/Empty",
                                    display_name=str(extra_tab_name))


@step(u'I am an edX user$')
def i_am_an_edx_user(step):
    world.create_user('robot')


@step(u'User "([^"]*)" is an edX user$')
def registered_edx_user(step, uname):
    world.create_user(uname)


def flush_xmodule_store():
    # Flush and initialize the module store
    # It needs the templates because it creates new records
    # by cloning from the template.
    # Note that if your test module gets in some weird state
    # (though it shouldn't), do this manually
    # from the bash shell to drop it:
    # $ mongo test_xmodule --eval "db.dropDatabase()"
    _MODULESTORES = {}
    modulestore().collection.drop()
    update_templates()

def course_id(course_num):
    return "%s/%s/%s" % (TEST_COURSE_ORG, course_num, 
                        TEST_COURSE_NAME.replace(" ", "_"))

def course_location(course_num):
    return Location(loc_or_tag="i4x",
                    org=TEST_COURSE_ORG,
                    course=course_num,
                    category='course',
                    name=TEST_COURSE_NAME.replace(" ", "_"))

def section_location(course_num):
    return Location(loc_or_tag="i4x",
                    org=TEST_COURSE_ORG,
                    course=course_num,
                    category='sequential',
                    name=TEST_SECTION_NAME.replace(" ", "_"))
