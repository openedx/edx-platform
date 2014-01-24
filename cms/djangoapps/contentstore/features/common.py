# pylint: disable=C0111
# pylint: disable=W0621

import time
import os
from lettuce import world, step
from nose.tools import assert_true, assert_in  # pylint: disable=no-name-in-module
from django.conf import settings

from student.roles import CourseRole, CourseStaffRole, CourseInstructorRole
from student.models import get_user

from selenium.webdriver.common.keys import Keys

from logging import getLogger
from student.tests.factories import AdminFactory
from student import auth
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
        css = 'a.action.delete-section-button'
    elif category == 'subsection':
        css = 'a.action.delete-subsection-button'
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

    # Because the notification uses a CSS transition,
    # Selenium will always report it as being visible.
    # This makes it very difficult to successfully click
    # the "Save" button at the UI level.
    # Instead, we use JavaScript to reliably click
    # the button.
    btn_css = 'div#page-notification a.action-%s' % name.lower()
    world.trigger_event(btn_css, event='focus')
    world.browser.execute_script("$('{}').click()".format(btn_css))
    world.wait_for_ajax_complete()


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
    global_admin = AdminFactory()
    for role in (CourseStaffRole, CourseInstructorRole):
        auth.add_users(global_admin, role(course.location), user)


def create_a_course():
    course = world.CourseFactory.create(org='MITx', course='999', display_name='Robot Super Course')
    world.scenario_dict['COURSE'] = course

    user = world.scenario_dict.get("USER")
    if not user:
        user = get_user('robot+studio@edx.org')

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


@world.absorb
def create_course_with_unit():
    """
    Prepare for tests by creating a course with a section, subsection, and unit.
    Performs the following:
        Clear out all courseware
        Create a course with a section, subsection, and unit
        Create a user and make that user a course author
        Log the user into studio
        Open the course from the dashboard
        Expand the section and click on the New Unit link
    The end result is the page where the user is editing the new unit
    """
    world.clear_courses()
    course = world.CourseFactory.create()
    world.scenario_dict['COURSE'] = course
    section = world.ItemFactory.create(parent_location=course.location)
    world.ItemFactory.create(
        parent_location=section.location,
        category='sequential',
        display_name='Subsection One',
    )
    user = create_studio_user(is_staff=False)
    add_course_author(user, course)

    log_into_studio()
    world.css_click('a.course-link')

    world.wait_for_js_to_load()
    css_selectors = [
        'div.section-item a.expand-collapse', 'a.new-unit-item'
    ]
    for selector in css_selectors:
        world.css_click(selector)

    world.wait_for_mathjax()
    world.wait_for_xmodule()

    assert world.is_css_present('ul.new-component-type')


@step('I have clicked the new unit button$')
@step(u'I am in Studio editing a new unit$')
def edit_new_unit(step):
    create_course_with_unit()


@step('the save notification button is disabled')
def save_button_disabled(step):
    button_css = '.action-save'
    disabled = 'is-disabled'
    assert world.css_has_class(button_css, disabled)


@step('the "([^"]*)" button is disabled')
def button_disabled(step, value):
    button_css = 'input[value="%s"]' % value
    assert world.css_has_class(button_css, 'is-disabled')


def _do_studio_prompt_action(intent, action):
    """
    Wait for a studio prompt to appear and press the specified action button
    See cms/static/js/views/feedback_prompt.js for implementation
    """
    assert intent in ['warning', 'error', 'confirmation', 'announcement',
        'step-required', 'help', 'mini']
    assert action in ['primary', 'secondary']

    world.wait_for_present('div.wrapper-prompt.is-shown#prompt-{}'.format(intent))

    action_css = 'li.nav-item > a.action-{}'.format(action)
    world.trigger_event(action_css, event='focus')
    world.browser.execute_script("$('{}').click()".format(action_css))

    world.wait_for_ajax_complete()
    world.wait_for_present('div.wrapper-prompt.is-hiding#prompt-{}'.format(intent))


@world.absorb
def confirm_studio_prompt():
    _do_studio_prompt_action('warning', 'primary')


@step('I confirm the prompt')
def confirm_the_prompt(step):
    confirm_studio_prompt()


@step(u'I am shown a prompt$')
def i_am_shown_a_notification(step):
    assert world.is_css_present('.wrapper-prompt')


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
    world.wait_for_ajax_complete()


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
    world.scenario_dict['USER'] = get_user(name + '@edx.org')


@step(u'the user "([^"]*)" exists( as a course (admin|staff member|is_staff))?$')
def create_other_user(_step, name, has_extra_perms, role_name):
    email = name + '@edx.org'
    user = create_studio_user(uname=name, password="test", email=email)
    if has_extra_perms:
        if role_name == "is_staff":
            user.is_staff = True
            user.save()
        else:
            if role_name == "admin":
                # admins get staff privileges, as well
                roles = (CourseStaffRole, CourseInstructorRole)
            else:
                roles = (CourseStaffRole,)
            location = world.scenario_dict["COURSE"].location
            global_admin = AdminFactory()
            for role in roles:
                auth.add_users(global_admin, role(location), user)


@step('I log out')
def log_out(_step):
    world.visit('logout')


@step(u'I click on "edit a draft"$')
def i_edit_a_draft(_step):
    world.css_click("a.create-draft")


@step(u'I click on "replace with draft"$')
def i_replace_w_draft(_step):
    world.css_click("a.publish-draft")


@step(u'I publish the unit$')
def publish_unit(_step):
    world.select_option('visibility-select', 'public')
