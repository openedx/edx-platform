from lettuce import world, step
from factories import *
from django.core.management import call_command
from lettuce.django import django_url
from django.conf import settings
from django.core.management import call_command
from nose.tools import assert_true
from nose.tools import assert_equal
import xmodule.modulestore.django

from logging import getLogger
logger = getLogger(__name__)

###########  STEP HELPERS ##############
@step('I (?:visit|access|open) the Studio homepage$')
def i_visit_the_studio_homepage(step):
    # To make this go to port 8001, put
    # LETTUCE_SERVER_PORT = 8001
    # in your settings.py file.
    world.browser.visit(django_url('/'))
    assert world.browser.is_element_present_by_css('body.no-header', 10)

@step('I am logged into Studio$')
def i_am_logged_into_studio(step):
    log_into_studio()

@step('I confirm the alert$')
def i_confirm_with_ok(step):
    world.browser.get_alert().accept()

@step(u'I press the "([^"]*)" delete icon$')
def i_press_the_category_delete_icon(step, category):
    if category == 'section':
        css = 'a.delete-button.delete-section-button span.delete-icon'
    elif category == 'subsection':
        css='a.delete-button.delete-subsection-button  span.delete-icon'
    else:
        assert False, 'Invalid category: %s' % category
    css_click(css)

####### HELPER FUNCTIONS ##############
def create_studio_user(
        uname='robot',
        email='robot+studio@edx.org',
        password='test',
        is_staff=False): 
    studio_user = UserFactory.build(
        username=uname, 
        email=email,
        password=password,
        is_staff=is_staff)
    studio_user.set_password(password)
    studio_user.save()

    registration = RegistrationFactory(user=studio_user)
    registration.register(studio_user)
    registration.activate()

    user_profile = UserProfileFactory(user=studio_user)

def flush_xmodule_store():
    # Flush and initialize the module store
    # It needs the templates because it creates new records
    # by cloning from the template.
    # Note that if your test module gets in some weird state
    # (though it shouldn't), do this manually
    # from the bash shell to drop it:
    # $ mongo test_xmodule --eval "db.dropDatabase()"
    xmodule.modulestore.django._MODULESTORES = {}
    xmodule.modulestore.django.modulestore().collection.drop()
    xmodule.templates.update_templates()

def assert_css_with_text(css,text):
    assert_true(world.browser.is_element_present_by_css(css, 5))
    assert_equal(world.browser.find_by_css(css).text, text)

def css_click(css):
    world.browser.find_by_css(css).first.click()

def css_fill(css, value):
    world.browser.find_by_css(css).first.fill(value)

def clear_courses():
    flush_xmodule_store()

def fill_in_course_info(
        name='Robot Super Course',
        org='MITx',
        num='101'):
    css_fill('.new-course-name',name)
    css_fill('.new-course-org',org)
    css_fill('.new-course-number',num)

def log_into_studio(
        uname='robot',
        email='robot+studio@edx.org',
        password='test',
        is_staff=False):
    create_studio_user(uname=uname, email=email, is_staff=is_staff)
    world.browser.cookies.delete()
    world.browser.visit(django_url('/'))
    world.browser.is_element_present_by_css('body.no-header', 10)

    login_form = world.browser.find_by_css('form#login_form')
    login_form.find_by_name('email').fill(email)
    login_form.find_by_name('password').fill(password)
    login_form.find_by_name('submit').click()

    assert_true(world.browser.is_element_present_by_css('.new-course-button', 5))

def create_a_course():
    css_click('a.new-course-button')
    fill_in_course_info()
    css_click('input.new-course-save')
    assert_true(world.browser.is_element_present_by_css('a#courseware-tab', 5))

def add_section(name='My Section'):
    link_css = 'a.new-courseware-section-button'
    css_click(link_css)
    name_css = '.new-section-name'
    save_css = '.new-section-name-save'
    css_fill(name_css,name)
    css_click(save_css)

def add_subsection(name='Subsection One'):
    css = 'a.new-subsection-item'
    css_click(css)
    name_css = 'input.new-subsection-name-input'
    save_css = 'input.new-subsection-name-save'
    css_fill(name_css, name)
    css_click(save_css)