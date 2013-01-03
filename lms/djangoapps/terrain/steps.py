from lettuce import world, step
from factories import *
from django.core.management import call_command
from lettuce.django import django_url
from django.conf import settings
from django.contrib.auth.models import User
from student.models import CourseEnrollment
from urllib import quote_plus
from nose.tools import assert_equals
from bs4 import BeautifulSoup
import time
import re
import os.path

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

@step(u'I press the "([^"]*)" button$')
def and_i_press_the_button(step, value):
    button_css = 'input[value="%s"]' % value
    world.browser.find_by_css(button_css).first.click()

@step('I should see that the path is "([^"]*)"$')
def i_should_see_that_the_path_is(step, path):
    assert world.browser.url == django_url(path)

@step(u'the page title should be "([^"]*)"$')
def the_page_title_should_be(step, title):
    assert_equals(world.browser.title, title)

@step('I am a logged in user$')
def i_am_logged_in_user(step):
    create_user('robot')
    log_in('robot@edx.org','test')

@step('I am not logged in$')
def i_am_not_logged_in(step):
    world.browser.cookies.delete()

@step('I am registered for a course$')
def i_am_registered_for_a_course(step):
    create_user('robot')
    u = User.objects.get(username='robot')
    CourseEnrollment.objects.get_or_create(user=u, course_id='MITx/6.002x/2012_Fall')

@step('I am registered for course "([^"]*)"$')
def i_am_registered_for_course_by_id(step, course_id):
    register_by_course_id(course_id)

@step('I am staff for course "([^"]*)"$')
def i_am_staff_for_course_by_id(step, course_id):
    register_by_course_id(course_id, True)

@step('I log in$')
def i_log_in(step):
    log_in('robot@edx.org','test')    

@step(u'I am an edX user$')
def i_am_an_edx_user(step):
    create_user('robot')

#### helper functions
@world.absorb
def create_user(uname):
    portal_user = UserFactory.build(username=uname, email=uname + '@edx.org')
    portal_user.set_password('test')
    portal_user.save()

    registration = RegistrationFactory(user=portal_user)
    registration.register(portal_user)
    registration.activate()

    user_profile = UserProfileFactory(user=portal_user)

@world.absorb
def log_in(email, password):   
    world.browser.cookies.delete()
    world.browser.visit(django_url('/'))
    world.browser.is_element_present_by_css('header.global', 10)       
    world.browser.click_link_by_href('#login-modal')
    login_form = world.browser.find_by_css('form#login_form')
    login_form.find_by_name('email').fill(email)
    login_form.find_by_name('password').fill(password)
    login_form.find_by_name('submit').click()

    # wait for the page to redraw
    assert world.browser.is_element_present_by_css('.content-wrapper', 10)

@world.absorb
def register_by_course_id(course_id, is_staff=False):
    create_user('robot')
    u = User.objects.get(username='robot')
    if is_staff:
        u.is_staff=True
        u.save()        
    CourseEnrollment.objects.get_or_create(user=u, course_id=course_id)

@world.absorb
def save_the_html(path='/tmp'):
    u = world.browser.url
    html = world.browser.html.encode('ascii', 'ignore')
    filename = '%s.html' % quote_plus(u)
    f = open('%s/%s' % (path, filename), 'w')
    f.write(html)
    f.close

@world.absorb
def save_the_course_content(path='/tmp'):
    html = world.browser.html.encode('ascii', 'ignore')
    soup = BeautifulSoup(html)

    # get rid of the header, we only want to compare the body
    soup.head.decompose()

    # for now, remove the data-id attributes, because they are 
    # causing mismatches between cms-master and master
    for item in soup.find_all(attrs={'data-id': re.compile('.*')}):
        del item['data-id']

    # we also need to remove them from unrendered problems, 
    # where they are contained in the text of divs instead of
    # in attributes of tags
    # Be careful of whether or not it was the last attribute
    # and needs a trailing space
    for item in soup.find_all(text=re.compile(' data-id=".*?" ')):
        s = unicode(item.string)
        item.string.replace_with(re.sub(' data-id=".*?" ', ' ', s))

    for item in soup.find_all(text=re.compile(' data-id=".*?"')):
        s = unicode(item.string)
        item.string.replace_with(re.sub(' data-id=".*?"', ' ', s))

    # prettify the html so it will compare better, with
    # each HTML tag on its own line
    output = soup.prettify()

    # use string slicing to grab everything after 'courseware/' in the URL
    u = world.browser.url
    section_url = u[u.find('courseware/')+11:] 

    if not os.path.exists(path):
        os.makedirs(path)

    filename = '%s.html' % (quote_plus(section_url))
    f = open('%s/%s' % (path, filename), 'w')
    f.write(output)
    f.close
