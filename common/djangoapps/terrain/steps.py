from lettuce import world, step
from .factories import *
from lettuce.django import django_url
from django.conf import settings
from django.http import HttpRequest
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from student.models import CourseEnrollment
from urllib import quote_plus
from nose.tools import assert_equals
from bs4 import BeautifulSoup
import time
import re
import os.path
from selenium.common.exceptions import WebDriverException

from logging import getLogger
logger = getLogger(__name__)


@step(u'I wait (?:for )?"(\d+)" seconds?$')
def wait(step, seconds):
    time.sleep(float(seconds))


@step('I reload the page$')
def reload_the_page(step):
    world.browser.reload()


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


@step(u'I click the link with the text "([^"]*)"$')
def click_the_link_with_the_text_group1(step, linktext):
    world.browser.find_link_by_text(linktext).first.click()


@step('I should see that the path is "([^"]*)"$')
def i_should_see_that_the_path_is(step, path):
    assert world.browser.url == django_url(path)


@step(u'the page title should be "([^"]*)"$')
def the_page_title_should_be(step, title):
    assert_equals(world.browser.title, title)


@step(u'the page title should contain "([^"]*)"$')
def the_page_title_should_contain(step, title):
    assert(title in world.browser.title)


@step('I am a logged in user$')
def i_am_logged_in_user(step):
    create_user('robot')
    log_in('robot', 'test')


@step('I am not logged in$')
def i_am_not_logged_in(step):
    world.browser.cookies.delete()


@step('I am staff for course "([^"]*)"$')
def i_am_staff_for_course_by_id(step, course_id):
    register_by_course_id(course_id, True)


@step('I log in$')
def i_log_in(step):
    log_in('robot', 'test')


@step(u'I am an edX user$')
def i_am_an_edx_user(step):
    create_user('robot')

#### helper functions


@world.absorb
def scroll_to_bottom():
    # Maximize the browser
    world.browser.execute_script("window.scrollTo(0, screen.height);")


@world.absorb
def create_user(uname):

    # If the user already exists, don't try to create it again
    if len(User.objects.filter(username=uname)) > 0:
        return

    portal_user = UserFactory.build(username=uname, email=uname + '@edx.org')
    portal_user.set_password('test')
    portal_user.save()

    registration = RegistrationFactory(user=portal_user)
    registration.register(portal_user)
    registration.activate()

    user_profile = UserProfileFactory(user=portal_user)


@world.absorb
def log_in(username, password):
    '''
    Log the user in programatically
    '''

    # Authenticate the user
    user = authenticate(username=username, password=password)
    assert(user is not None and user.is_active)

    # Send a fake HttpRequest to log the user in
    # We need to process the request using
    # Session middleware and Authentication middleware
    # to ensure that session state can be stored
    request = HttpRequest()
    SessionMiddleware().process_request(request)
    AuthenticationMiddleware().process_request(request)
    login(request, user)

    # Save the session
    request.session.save()

    # Retrieve the sessionid and add it to the browser's cookies
    cookie_dict = {settings.SESSION_COOKIE_NAME: request.session.session_key}
    try:
        world.browser.cookies.add(cookie_dict)

    # WebDriver has an issue where we cannot set cookies
    # before we make a GET request, so if we get an error,
    # we load the '/' page and try again
    except:
        world.browser.visit(django_url('/'))
        world.browser.cookies.add(cookie_dict)


@world.absorb
def register_by_course_id(course_id, is_staff=False):
    create_user('robot')
    u = User.objects.get(username='robot')
    if is_staff:
        u.is_staff = True
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
    section_url = u[u.find('courseware/') + 11:]


    if not os.path.exists(path):
        os.makedirs(path)

    filename = '%s.html' % (quote_plus(section_url))
    f = open('%s/%s' % (path, filename), 'w')
    f.write(output)
    f.close

@world.absorb
def css_click(css_selector):
    try:
        world.browser.find_by_css(css_selector).click()

    except WebDriverException:
        # Occassionally, MathJax or other JavaScript can cover up
        # an element  temporarily.
        # If this happens, wait a second, then try again
        time.sleep(1)
        world.browser.find_by_css(css_selector).click()
