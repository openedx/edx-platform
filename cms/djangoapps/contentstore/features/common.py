from lettuce import world, step
from lettuce.django import django_url
from nose.tools import assert_true
from nose.tools import assert_equal
from selenium.webdriver.support.ui import WebDriverWait

from terrain.factories import UserFactory, RegistrationFactory, UserProfileFactory
from terrain.factories import CourseFactory, GroupFactory
import xmodule.modulestore.django
from auth.authz import get_user_by_email

from logging import getLogger
logger = getLogger(__name__)

###########  STEP HELPERS ##############


@step('I (?:visit|access|open) the Studio homepage$')
def i_visit_the_studio_homepage(step):
    # To make this go to port 8001, put
    # LETTUCE_SERVER_PORT = 8001
    # in your settings.py file.
    world.browser.visit(django_url('/'))
    signin_css = 'a.action-signin'
    assert world.browser.is_element_present_by_css(signin_css, 10)


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
        css = 'a.delete-button.delete-subsection-button  span.delete-icon'
    else:
        assert False, 'Invalid category: %s' % category
    css_click(css)


@step('I have opened a new course in Studio$')
def i_have_opened_a_new_course(step):
    clear_courses()
    log_into_studio()
    create_a_course()

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


def assert_css_with_text(css, text):
    assert_true(world.browser.is_element_present_by_css(css, 5))
    assert_equal(world.browser.find_by_css(css).text, text)


def css_click(css):
    assert_true(world.browser.is_element_present_by_css(css, 5))
    world.browser.find_by_css(css).first.click()


def css_click_at(css, x=10, y=10):
    '''
    A method to click at x,y coordinates of the element
    rather than in the center of the element
    '''
    assert_true(world.browser.is_element_present_by_css(css, 5))
    e = world.browser.find_by_css(css).first
    e.action_chains.move_to_element_with_offset(e._element, x, y)
    e.action_chains.click()
    e.action_chains.perform()


def css_fill(css, value):
    world.browser.find_by_css(css).first.fill(value)


def css_find(css):
    return world.browser.find_by_css(css)


def wait_for(func):
    WebDriverWait(world.browser.driver, 10).until(func)


def id_find(id):
    return world.browser.find_by_id(id)


def clear_courses():
    flush_xmodule_store()


def fill_in_course_info(
        name='Robot Super Course',
        org='MITx',
        num='101'):
    css_fill('.new-course-name', name)
    css_fill('.new-course-org', org)
    css_fill('.new-course-number', num)


def log_into_studio(
        uname='robot',
        email='robot+studio@edx.org',
        password='test',
        is_staff=False):
    create_studio_user(uname=uname, email=email, is_staff=is_staff)
    world.browser.cookies.delete()
    world.browser.visit(django_url('/'))
    signin_css = 'a.action-signin'
    world.browser.is_element_present_by_css(signin_css, 10)

    # click the signin button
    css_click(signin_css)

    login_form = world.browser.find_by_css('form#login_form')
    login_form.find_by_name('email').fill(email)
    login_form.find_by_name('password').fill(password)
    login_form.find_by_name('submit').click()

    assert_true(world.browser.is_element_present_by_css('.new-course-button', 5))


def create_a_course():
    c = CourseFactory.create(org='MITx', course='999', display_name='Robot Super Course')

    # Add the user to the instructor group of the course
    # so they will have the permissions to see it in studio
    g = GroupFactory.create(name='instructor_MITx/999/Robot_Super_Course')
    u = get_user_by_email('robot+studio@edx.org')
    u.groups.add(g)
    u.save()
    world.browser.reload()

    course_link_css = 'span.class-name'
    css_click(course_link_css)
    course_title_css = 'span.course-title'
    assert_true(world.browser.is_element_present_by_css(course_title_css, 5))


def add_section(name='My Section'):
    link_css = 'a.new-courseware-section-button'
    css_click(link_css)
    name_css = 'input.new-section-name'
    save_css = 'input.new-section-name-save'
    css_fill(name_css, name)
    css_click(save_css)
    span_css = 'span.section-name-span'
    assert_true(world.browser.is_element_present_by_css(span_css, 5))


def add_subsection(name='Subsection One'):
    css = 'a.new-subsection-item'
    css_click(css)
    name_css = 'input.new-subsection-name-input'
    save_css = 'input.new-subsection-name-save'
    css_fill(name_css, name)
    css_click(save_css)
