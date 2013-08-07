# pylint: disable=C0111
# pylint: disable=W0621

from lettuce import world, step
from nose.tools import assert_true

from auth.authz import get_user_by_email, get_course_groupname_for_role

from selenium.webdriver.common.keys import Keys
import time
from django.contrib.auth.models import Group

from logging import getLogger
logger = getLogger(__name__)

from terrain.browser import reset_data

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


@step('(I select|s?he selects) the new course')
def select_new_course(_step, whom):
    course_link_css = 'a.course-link'
    world.css_click(course_link_css)


@step(u'I press the "([^"]*)" notification button$')
def press_the_notification_button(_step, name):
    css = 'a.action-%s' % name.lower()

    # The button was clicked if either the notification bar is gone,
    # or we see an error overlaying it (expected for invalid inputs).
    def button_clicked():
        confirmation_dismissed = world.is_css_not_present('.is-shown.wrapper-notification-warning')
        error_showing = world.is_css_present('.is-shown.wrapper-notification-error')
        return confirmation_dismissed or error_showing

    world.css_click(css, success_condition=button_clicked), '%s button not clicked after 5 attempts.' % name


@step('I change the "(.*)" field to "(.*)"$')
def i_change_field_to_value(_step, field, value):
    field_css = '#%s' % '-'.join([s.lower() for s in field.split()])
    ele = world.css_find(field_css).first
    ele.fill(value)
    ele._element.send_keys(Keys.ENTER)


@step('I reset the database')
def reset_the_db(_step):
    """
    When running Lettuce tests using examples (i.e. "Confirmation is
    shown on save" in course-settings.feature), the normal hooks
    aren't called between examples. reset_data should run before each
    scenario to flush the test database. When this doesn't happen we
    get errors due to trying to insert a non-unique entry. So instead,
    we delete the database manually. This has the effect of removing
    any users and courses that have been created during the test run.
    """
    reset_data(None)


@step('I see a confirmation that my changes have been saved')
def i_see_a_confirmation(step):
    confirmation_css = '#alert-confirmation'
    assert world.is_css_present(confirmation_css)


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

    return studio_user


def fill_in_course_info(
        name='Robot Super Course',
        org='MITx',
        num='101',
        run='2013_Spring'):
    world.css_fill('.new-course-name', name)
    world.css_fill('.new-course-org', org)
    world.css_fill('.new-course-number', num)
    world.css_fill('.new-course-run', run)


def log_into_studio(
        uname='robot',
        email='robot+studio@edx.org',
        password='test'):

    world.browser.cookies.delete()
    world.visit('/')

    signin_css = 'a.action-signin'
    world.is_css_present(signin_css)
    world.css_click(signin_css)

    def fill_login_form():
        login_form = world.browser.find_by_css('form#login_form')
        login_form.find_by_name('email').fill(email)
        login_form.find_by_name('password').fill(password)
        login_form.find_by_name('submit').click()
    world.retry_on_exception(fill_login_form)
    assert_true(world.is_css_present('.new-course-button'))
    world.scenario_dict['USER'] = get_user_by_email(email)


def create_a_course():
    course = world.CourseFactory.create(org='MITx', course='999', display_name='Robot Super Course')
    world.scenario_dict['COURSE'] = course

    user = world.scenario_dict.get("USER")
    if not user:
        user = get_user_by_email('robot+studio@edx.org')

    # Add the user to the instructor group of the course
    # so they will have the permissions to see it in studio
    for role in ("staff", "instructor"):
        groupname = get_course_groupname_for_role(course.location, role)
        group, __ = Group.objects.get_or_create(name=groupname)
        user.groups.add(group)
    user.save()
    world.browser.reload()
    course_link_css = 'a.course-link'
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
        'video',
        '.xmodule_VideoModule',
        has_multiple_templates=False
    )


@step('I have created a Video Alpha component$')
def i_created_video_alpha(step):
    step.given('I have enabled the videoalpha advanced module')
    world.css_click('a.course-link')
    step.given('I have added a new subsection')
    step.given('I expand the first section')
    world.css_click('a.new-unit-item')
    world.css_click('.large-advanced-icon')
    world.click_component_from_menu('videoalpha', None, '.xmodule_VideoAlphaModule')


@step('I have enabled the (.*) advanced module$')
def i_enabled_the_advanced_module(step, module):
    step.given('I have opened a new course section in Studio')
    world.css_click('.nav-course-settings')
    world.css_click('.nav-course-settings-advanced')
    type_in_codemirror(0, '["%s"]' % module)
    press_the_notification_button(step, 'Save')


@step('I have clicked the new unit button')
def open_new_unit(step):
    step.given('I have opened a new course section in Studio')
    step.given('I have added a new subsection')
    step.given('I expand the first section')
    world.css_click('a.new-unit-item')


@step('when I view the (video.*) it (.*) show the captions')
def shows_captions(_step, video_type, show_captions):
    # Prevent cookies from overriding course settings
    world.browser.cookies.delete('hide_captions')
    if show_captions == 'does not':
        assert world.css_has_class('.%s' % video_type, 'closed')
    else:
        assert world.is_css_not_present('.%s.closed' % video_type)


@step('the save button is disabled$')
def save_button_disabled(step):
    button_css = '.action-save'
    disabled = 'is-disabled'
    assert world.css_has_class(button_css, disabled)


@step('I confirm the prompt')
def confirm_the_prompt(step):
    prompt_css = 'a.button.action-primary'
    world.css_click(prompt_css, success_condition=lambda: not world.css_visible(prompt_css))


@step(u'I am shown a (.*)$')
def i_am_shown_a_notification(step, notification_type):
    assert world.is_css_present('.wrapper-%s' % notification_type)


def type_in_codemirror(index, text):
    world.css_click(".CodeMirror", index=index)
    world.browser.execute_script("$('div.CodeMirror.CodeMirror-focused > div').css('overflow', '')")
    g = world.css_find("div.CodeMirror.CodeMirror-focused > div > textarea")
    if world.is_mac():
        g._element.send_keys(Keys.COMMAND + 'a')
    else:
        g._element.send_keys(Keys.CONTROL + 'a')
    g._element.send_keys(Keys.DELETE)
    g._element.send_keys(text)
