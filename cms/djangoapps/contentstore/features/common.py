# pylint: disable=C0111
# pylint: disable=W0621

from lettuce import world, step
from nose.tools import assert_true

from auth.authz import get_user_by_email

from selenium.webdriver.common.keys import Keys
import time

from logging import getLogger
logger = getLogger(__name__)

_COURSE_NAME = 'Robot Super Course'
_COURSE_NUM = '999'
_COURSE_ORG = 'MITx'

###########  STEP HELPERS ##############


@step('I (?:visit|access|open) the Studio homepage$')
def i_visit_the_studio_homepage(_step):
    # To make this go to port 8001, put
    # LETTUCE_SERVER_PORT = 8001
    # in your settings.py file.
    world.visit('/')
    signin_css = 'a.action-signin'
    assert world.is_css_present(signin_css)


@step('I am logged into Studio$')
def i_am_logged_into_studio(_step):
    log_into_studio()


@step('I confirm the alert$')
def i_confirm_with_ok(_step):
    world.browser.get_alert().accept()


@step(u'I press the "([^"]*)" delete icon$')
def i_press_the_category_delete_icon(_step, category):
    if category == 'section':
        css = 'a.delete-button.delete-section-button span.delete-icon'
    elif category == 'subsection':
        css = 'a.delete-button.delete-subsection-button  span.delete-icon'
    else:
        assert False, 'Invalid category: %s' % category
    world.css_click(css)


@step('I have opened a new course in Studio$')
def i_have_opened_a_new_course(_step):
    open_new_course()


####### HELPER FUNCTIONS ##############
def open_new_course():
    world.clear_courses()
    create_studio_user()
    log_into_studio()
    create_a_course()


def create_studio_user(
        uname='robot',
        email='robot+studio@edx.org',
        password='test',
        is_staff=False):
    studio_user = world.UserFactory(
        username=uname,
        email=email,
        password=password,
        is_staff=is_staff)

    registration = world.RegistrationFactory(user=studio_user)
    registration.register(studio_user)
    registration.activate()


def fill_in_course_info(
        name=_COURSE_NAME,
        org=_COURSE_ORG,
        num=_COURSE_NUM):
    world.css_fill('.new-course-name', name)
    world.css_fill('.new-course-org', org)
    world.css_fill('.new-course-number', num)


def log_into_studio(
        uname='robot',
        email='robot+studio@edx.org',
        password='test'):

    world.browser.cookies.delete()
    world.visit('/')

    signin_css = 'a.action-signin'
    world.is_css_present(signin_css)
    world.css_click(signin_css)

    login_form = world.browser.find_by_css('form#login_form')
    login_form.find_by_name('email').fill(email)
    login_form.find_by_name('password').fill(password)
    login_form.find_by_name('submit').click()

    assert_true(world.is_css_present('.new-course-button'))


def create_a_course():
    world.CourseFactory.create(org=_COURSE_ORG, course=_COURSE_NUM, display_name=_COURSE_NAME)

    # Add the user to the instructor group of the course
    # so they will have the permissions to see it in studio
    course = world.GroupFactory.create(name='instructor_MITx/{course_num}/{course_name}'.format(course_num=_COURSE_NUM, course_name=_COURSE_NAME.replace(" ", "_")))
    user = get_user_by_email('robot+studio@edx.org')
    user.groups.add(course)
    user.save()
    world.browser.reload()

    course_link_css = 'span.class-name'
    world.css_click(course_link_css)
    course_title_css = 'span.course-title'
    assert_true(world.is_css_present(course_title_css))


def add_section(name='My Section'):
    link_css = 'a.new-courseware-section-button'
    world.css_click(link_css)
    name_css = 'input.new-section-name'
    save_css = 'input.new-section-name-save'
    world.css_fill(name_css, name)
    world.css_click(save_css)
    span_css = 'span.section-name-span'
    assert_true(world.is_css_present(span_css))


def add_subsection(name='Subsection One'):
    css = 'a.new-subsection-item'
    world.css_click(css)
    name_css = 'input.new-subsection-name-input'
    save_css = 'input.new-subsection-name-save'
    world.css_fill(name_css, name)
    world.css_click(save_css)


def set_date_and_time(date_css, desired_date, time_css, desired_time):
    world.css_fill(date_css, desired_date)
    # hit TAB to get to the time field
    e = world.css_find(date_css).first
    # pylint: disable=W0212
    e._element.send_keys(Keys.TAB)
    world.css_fill(time_css, desired_time)
    e = world.css_find(time_css).first
    e._element.send_keys(Keys.TAB)
    time.sleep(float(1))


@step('I have created a Video component$')
def i_created_a_video_component(step):
    world.create_component_instance(
        step, '.large-video-icon',
        'i4x://edx/templates/video/default',
        '.xmodule_VideoModule'
    )


@step('I have clicked the new unit button')
def open_new_unit(step):
    step.given('I have opened a new course section in Studio')
    step.given('I have added a new subsection')
    step.given('I expand the first section')
    world.css_click('a.new-unit-item')


@step('when I view the video it (.*) show the captions')
def shows_captions(step, show_captions):
    # Prevent cookies from overriding course settings
    world.browser.cookies.delete('hide_captions')
    if show_captions == 'does not':
        assert world.css_find('.video')[0].has_class('closed')
    else:
        assert world.is_css_not_present('.video.closed')


def type_in_codemirror(index, text):
    world.css_click(".CodeMirror", index=index)
    g = world.css_find("div.CodeMirror.CodeMirror-focused > div > textarea")
    if world.is_mac():
        g._element.send_keys(Keys.COMMAND + 'a')
    else:
        g._element.send_keys(Keys.CONTROL + 'a')
    g._element.send_keys(Keys.DELETE)
    g._element.send_keys(text)
