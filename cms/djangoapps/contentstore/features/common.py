# pylint: disable=C0111
# pylint: disable=W0621

from lettuce import world, step
from nose.tools import assert_true, assert_in, assert_false  # pylint: disable=E0611

from auth.authz import get_user_by_email, get_course_groupname_for_role
from django.conf import settings

from selenium.webdriver.common.keys import Keys
import time
import os
from django.contrib.auth.models import Group

from logging import getLogger
logger = getLogger(__name__)

from terrain.browser import reset_data

TEST_ROOT = settings.COMMON_TEST_DATA_ROOT


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
    # TODO: fix up this code. Selenium is not dealing well with css transforms,
    # as it thinks that the notification and the buttons are always visible

    # First wait for the notification to pop up
    notification_css = 'div#page-notification div.wrapper-notification'
    world.wait_for_visible(notification_css)

    # You would think that the above would have worked, but it doesn't.
    # Brute force wait for now.
    world.wait(.5)

    # Now make sure the button is there
    btn_css = 'div#page-notification a.action-%s' % name.lower()
    world.wait_for_visible(btn_css)

    # You would think that the above would have worked, but it doesn't.
    # Brute force wait for now.
    world.wait(.5)

    if world.is_firefox():
        # This is done to explicitly make the changes save on firefox.
        # It will remove focus from the previously focused element
        world.trigger_event(btn_css, event='focus')
        world.browser.execute_script("$('{}').click()".format(btn_css))
    else:
        world.css_click(btn_css)


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
        password='test',
        name='Robot Studio'):

    world.log_in(username=uname, password=password, email=email, name=name)
    # Navigate to the studio dashboard
    world.visit('/')
    assert_in(uname, world.css_text('h2.title', timeout=10))


def add_course_author(user, course):
    """
    Add the user to the instructor group of the course
    so they will have the permissions to see it in studio
    """
    for role in ("staff", "instructor"):
        groupname = get_course_groupname_for_role(course.location, role)
        group, __ = Group.objects.get_or_create(name=groupname)
        user.groups.add(group)
    user.save()


def create_a_course():
    course = world.CourseFactory.create(org='MITx', course='999', display_name='Robot Super Course')
    world.scenario_dict['COURSE'] = course

    user = world.scenario_dict.get("USER")
    if not user:
        user = get_user_by_email('robot+studio@edx.org')

    add_course_author(user, course)

    # Navigate to the studio dashboard
    world.visit('/')
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


@step('I have enabled the (.*) advanced module$')
def i_enabled_the_advanced_module(step, module):
    step.given('I have opened a new course section in Studio')
    world.css_click('.nav-course-settings')
    world.css_click('.nav-course-settings-advanced a')
    type_in_codemirror(0, '["%s"]' % module)
    press_the_notification_button(step, 'Save')


@step('I have clicked the new unit button')
def open_new_unit(step):
    step.given('I have opened a new course section in Studio')
    step.given('I have added a new subsection')
    step.given('I expand the first section')
    world.css_click('a.new-unit-item')


@step('the save notification button is disabled')
def save_button_disabled(step):
    button_css = '.action-save'
    disabled = 'is-disabled'
    assert world.css_has_class(button_css, disabled)


@step('the "([^"]*)" button is disabled')
def button_disabled(step, value):
    button_css = 'input[value="%s"]' % value
    assert world.css_has_class(button_css, 'is-disabled')


@step('I confirm the prompt')
def confirm_the_prompt(step):

    def click_button(btn_css):
        world.css_click(btn_css)
        return world.css_find(btn_css).visible == False

    prompt_css = 'div.prompt.has-actions'
    world.wait_for_visible(prompt_css)

    btn_css = 'a.button.action-primary'
    world.wait_for_visible(btn_css)

    # Sometimes you can do a click before the prompt is up.
    # Thus we need some retry logic here.
    world.wait_for(lambda _driver: click_button(btn_css))

    assert_false(world.css_find(btn_css).visible)


@step(u'I am shown a (.*)$')
def i_am_shown_a_notification(step, notification_type):
    assert world.is_css_present('.wrapper-%s' % notification_type)


def type_in_codemirror(index, text):
    world.wait(1)  # For now, slow this down so that it works. TODO: fix it.
    world.css_click("div.CodeMirror-lines", index=index)
    world.browser.execute_script("$('div.CodeMirror.CodeMirror-focused > div').css('overflow', '')")
    g = world.css_find("div.CodeMirror.CodeMirror-focused > div > textarea")
    if world.is_mac():
        g._element.send_keys(Keys.COMMAND + 'a')
    else:
        g._element.send_keys(Keys.CONTROL + 'a')
    g._element.send_keys(Keys.DELETE)
    g._element.send_keys(text)
    if world.is_firefox():
        world.trigger_event('div.CodeMirror', index=index, event='blur')


def upload_file(filename):
    path = os.path.join(TEST_ROOT, filename)
    world.browser.execute_script("$('input.file-input').css('display', 'block')")
    world.browser.attach_file('file', os.path.abspath(path))
    button_css = '.upload-dialog .action-upload'
    world.css_click(button_css)


@step(u'"([^"]*)" logs in$')
def other_user_login(step, name):
    step.given('I log out')
    world.visit('/')

    signin_css = 'a.action-signin'
    world.is_css_present(signin_css)
    world.css_click(signin_css)

    def fill_login_form():
        login_form = world.browser.find_by_css('form#login_form')
        login_form.find_by_name('email').fill(name + '@edx.org')
        login_form.find_by_name('password').fill("test")
        login_form.find_by_name('submit').click()
    world.retry_on_exception(fill_login_form)
    assert_true(world.is_css_present('.new-course-button'))
    world.scenario_dict['USER'] = get_user_by_email(name + '@edx.org')


@step(u'the user "([^"]*)" exists( as a course (admin|staff member|is_staff))?$')
def create_other_user(_step, name, has_extra_perms, role_name):
    email = name + '@edx.org'
    user = create_studio_user(uname=name, password="test", email=email)
    if has_extra_perms:
        if role_name == "is_staff":
            user.is_staff = True
        else:
            if role_name == "admin":
                # admins get staff privileges, as well
                roles = ("staff", "instructor")
            else:
                roles = ("staff",)
            location = world.scenario_dict["COURSE"].location
            for role in roles:
                groupname = get_course_groupname_for_role(location, role)
                group, __ = Group.objects.get_or_create(name=groupname)
                user.groups.add(group)
        user.save()


@step('I log out')
def log_out(_step):
    world.visit('logout')
