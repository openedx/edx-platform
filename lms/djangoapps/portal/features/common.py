from lettuce import world, step#, before, after
from factories import *
from django.core.management import call_command
from salad.steps.everything import *
from lettuce.django import django_url
from django.conf import settings
from django.contrib.auth.models import User
from student.models import CourseEnrollment
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

@step('I am logged in$')
def i_am_logged_in(step):

    # This is a workaround for now, until askbot is removed
    # because askbot is messing with the user and auth tables.
    call_command('loaddata', '/tmp/fixtures/robot_user_active.json')
    world.browser.cookies.delete()
    world.browser.visit(django_url('/'))
    world.browser.is_element_present_by_css('header.global', 10)       
    world.browser.click_link_by_href('#login-modal')
    login_form = world.browser.find_by_css('form#login_form')
    login_form.find_by_name('email').fill('robot@edx.org')
    login_form.find_by_name('password').fill('test')
    login_form.find_by_name('submit').click()

    # wait for the page to redraw
    assert world.browser.is_element_present_by_css('.content-wrapper', 5)

@step('I am not logged in$')
def i_am_not_logged_in(step):
    world.browser.cookies.delete()

@step(u'I am registered for a course$')
def i_am_registered_for_a_course(step):
    u = User.objects.get(username='robot2')
    CourseEnrollment.objects.create(user=u, course_id='MITx/6.002x/2012_Fall')

@step(u'I am an edX user$')
def i_am_an_edx_user(step):
    call_command('loaddata', '/tmp/fixtures/robot_user_active.json')

###########  USER CREATION ##############
@step(u'User "([^"]*)" is an edX user$')
def registered_edx_user(step, uname):
    # This user factory stuff should work after we kill askbot
    # portal_user = UserFactory.build(username=uname, email=uname + '@edx.org')
    # portal_user.set_password('test')
    # portal_user.save()

    # registration = RegistrationFactory(user=portal_user)
    # registration.register(portal_user)
    # registration.activate()

    # user_profile = UserProfileFactory(user=portal_user)

    # This is a workaround for now, until askbot is removed
    # because askbot is messing with the user and auth tables.
    call_command('loaddata', '/tmp/fixtures/robot_user_active.json')

###########  DEBUGGING ##############
@step(u'I save a screenshot to "(.*)"')
def save_screenshot_to(step, filename):
    world.browser.driver.save_screenshot(filename)
    
