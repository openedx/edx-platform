# pylint: disable=missing-docstring
# pylint: disable=redefined-outer-name

import os
from lettuce import world, step
from nose.tools import assert_true, assert_in  # pylint: disable=no-name-in-module
from django.conf import settings

from student.roles import CourseStaffRole, CourseInstructorRole, GlobalStaff
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


@step('I have populated a new course in Studio$')
def i_have_populated_a_new_course(_step):
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
    assert_in(uname, world.css_text('span.account-username', timeout=10))


def add_course_author(user, course):
    """
    Add the user to the instructor group of the course
    so they will have the permissions to see it in studio
    """
    global_admin = AdminFactory()
    for role in (CourseStaffRole, CourseInstructorRole):
        auth.add_users(global_admin, role(course.id), user)


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


def add_section():
    world.css_click('.outline .button-new')
    assert_true(world.is_css_present('.outline-section .xblock-field-value'))


def set_date_and_time(date_css, desired_date, time_css, desired_time, key=None):
    set_element_value(date_css, desired_date, key)
    world.wait_for_ajax_complete()

    set_element_value(time_css, desired_time, key)
    world.wait_for_ajax_complete()


def set_element_value(element_css, element_value, key=None):
    element = world.css_find(element_css).first
    element.fill(element_value)
    # hit TAB or provided key to trigger save content
    if key is not None:
        element._element.send_keys(getattr(Keys, key))  # pylint: disable=protected-access
    else:
        element._element.send_keys(Keys.TAB)  # pylint: disable=protected-access


@step('I have enabled the (.*) advanced module$')
def i_enabled_the_advanced_module(step, module):
    step.given('I have opened a new course section in Studio')
    world.css_click('.nav-course-settings')
    world.css_click('.nav-course-settings-advanced a')
    type_in_codemirror(0, '["%s"]' % module)
    press_the_notification_button(step, 'Save')


@world.absorb
def create_unit_from_course_outline():
    """
    Expands the section and clicks on the New Unit link.
    The end result is the page where the user is editing the new unit.
    """
    css_selectors = [
        '.outline-subsection .expand-collapse', '.outline-subsection .button-new'
    ]
    for selector in css_selectors:
        world.css_click(selector)

    world.wait_for_mathjax()
    world.wait_for_xmodule()
    world.wait_for_loading()

    assert world.is_css_present('ul.new-component-type')


@world.absorb
def wait_for_loading():
    """
    Waits for the loading indicator to be hidden.
    """
    world.wait_for(lambda _driver: len(world.browser.find_by_css('div.ui-loading.is-hidden')) > 0)


@step('I have clicked the new unit button$')
@step(u'I am in Studio editing a new unit$')
def edit_new_unit(step):
    step.given('I have populated a new course in Studio')
    create_unit_from_course_outline()


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
    assert intent in [
        'warning',
        'error',
        'confirmation',
        'announcement',
        'step-required',
        'help',
        'mini',
    ]
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


def type_in_codemirror(index, text, find_prefix="$"):
    script = """
    var cm = {find_prefix}('div.CodeMirror:eq({index})').get(0).CodeMirror;
    cm.getInputField().focus();
    cm.setValue(arguments[0]);
    cm.getInputField().blur();""".format(index=index, find_prefix=find_prefix)
    world.browser.driver.execute_script(script, str(text))
    world.wait_for_ajax_complete()


def get_codemirror_value(index=0, find_prefix="$"):
    return world.browser.driver.execute_script(
        """
        return {find_prefix}('div.CodeMirror:eq({index})').get(0).CodeMirror.getValue();
        """.format(index=index, find_prefix=find_prefix)
    )


def attach_file(filename, sub_path):
    path = os.path.join(TEST_ROOT, sub_path, filename)
    world.browser.execute_script("$('input.file-input').css('display', 'block')")
    assert_true(os.path.exists(path))
    world.browser.attach_file('file', os.path.abspath(path))


def upload_file(filename, sub_path=''):
    # The file upload dialog is a faux modal, a div that takes over the display
    attach_file(filename, sub_path)
    modal_css = 'div.wrapper-modal-window-assetupload'
    button_css = '{} .action-upload'.format(modal_css)
    world.css_click(button_css)

    # Clicking the Upload button triggers an AJAX POST.
    world.wait_for_ajax_complete()

    # The modal stays up with a "File uploaded succeeded" confirmation message, then goes away.
    # It should take under 2 seconds, so wait up to 10.
    # Note that is_css_not_present will return as soon as the element is gone.
    assert world.is_css_not_present(modal_css, wait_time=10)


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
            GlobalStaff().add_users(user)
        else:
            if role_name == "admin":
                # admins get staff privileges, as well
                roles = (CourseStaffRole, CourseInstructorRole)
            else:
                roles = (CourseStaffRole,)
            course_key = world.scenario_dict["COURSE"].id
            global_admin = AdminFactory()
            for role in roles:
                auth.add_users(global_admin, role(course_key), user)


@step('I log out')
def log_out(_step):
    world.visit('logout')
