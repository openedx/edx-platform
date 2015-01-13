# pylint: disable=missing-docstring
# pylint: disable=redefined-outer-name

# Disable the "wildcard import" warning so we can bring in all methods from
# course helpers and ui helpers
# pylint: disable=wildcard-import

# Disable the "Unused import %s from wildcard import" warning
# pylint: disable=unused-wildcard-import

# Disable the "unused argument" warning because lettuce uses "step"
# pylint: disable=unused-argument

# django_url is assigned late in the process of loading lettuce,
# so we import this as a module, and then read django_url from
# it to get the correct value
import lettuce.django
from django.conf import settings

from lettuce import world, step
from .course_helpers import *
from .ui_helpers import *
from nose.tools import assert_equals  # pylint: disable=no-name-in-module

from opaque_keys.edx.locations import SlashSeparatedCourseKey

from logging import getLogger
logger = getLogger(__name__)


@step(r'I wait (?:for )?"(\d+\.?\d*)" seconds?$')
def wait_for_seconds(step, seconds):
    world.wait(seconds)


@step('I reload the page$')
def reload_the_page(step):
    world.wait_for_ajax_complete()
    world.browser.reload()
    world.wait_for_js_to_load()


@step('I press the browser back button$')
def browser_back(step):
    world.browser.driver.back()


@step('I (?:visit|access|open) the homepage$')
def i_visit_the_homepage(step):
    world.visit('/')
    assert world.is_css_present('header.global')


@step(u'I (?:visit|access|open) the dashboard$')
def i_visit_the_dashboard(step):
    world.visit('/dashboard')
    assert world.is_css_present('section.container.dashboard')


@step('I should be on the dashboard page$')
def i_should_be_on_the_dashboard(step):
    assert world.is_css_present('section.container.dashboard')
    assert 'Dashboard' in world.browser.title


@step(u'I (?:visit|access|open) the courses page$')
def i_am_on_the_courses_page(step):
    world.visit('/courses')
    assert world.is_css_present('div.courses')


@step(u'I press the "([^"]*)" button$')
def and_i_press_the_button(step, value):
    button_css = 'input[value="%s"]' % value
    world.css_click(button_css)


@step(u'I click the link with the text "([^"]*)"$')
def click_the_link_with_the_text_group1(step, linktext):
    world.click_link(linktext)


@step('I should see that the path is "([^"]*)"$')
def i_should_see_that_the_path_is(step, path):
    if 'COURSE' in world.scenario_dict:
        path = path.format(world.scenario_dict['COURSE'].id)
    assert world.url_equals(path), (
        "path should be {!r} but is {!r}".format(path, world.browser.url)
    )


@step(u'the page title should be "([^"]*)"$')
def the_page_title_should_be(step, title):
    assert_equals(world.browser.title, title)


@step(u'the page title should contain "([^"]*)"$')
def the_page_title_should_contain(step, title):
    assert title in world.browser.title


@step('I log in$')
def i_log_in(step):
    world.log_in(username='robot', password='test')


@step('I am a logged in user$')
def i_am_logged_in_user(step):
    world.create_user('robot', 'test')
    world.log_in(username='robot', password='test')


@step('I am not logged in$')
def i_am_not_logged_in(step):
    world.visit('logout')


@step('I am staff for course "([^"]*)"$')
def i_am_staff_for_course_by_id(step, course_id):
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    world.register_by_course_key(course_key, True)


@step(r'click (?:the|a) link (?:called|with the text) "([^"]*)"$')
def click_the_link_called(step, text):
    world.click_link(text)


@step(r'should see that the url is "([^"]*)"$')
def should_have_the_url(step, url):
    assert_equals(world.browser.url, url)


@step(r'should see (?:the|a) link (?:called|with the text) "([^"]*)"$')
def should_see_a_link_called(step, text):
    assert len(world.browser.find_link_by_text(text)) > 0


@step(r'should see (?:the|a) link with the id "([^"]*)" called "([^"]*)"$')
def should_have_link_with_id_and_text(step, link_id, text):
    link = world.browser.find_by_id(link_id)
    assert len(link) > 0
    assert_equals(link.text, text)


@step(r'should see a link to "([^"]*)" with the text "([^"]*)"$')
def should_have_link_with_path_and_text(step, path, text):
    link = world.browser.find_link_by_text(text)
    assert len(link) > 0
    assert_equals(link.first["href"], lettuce.django.django_url(path))


@step(r'should( not)? see "(.*)" (?:somewhere|anywhere) (?:in|on) (?:the|this) page')
def should_see_in_the_page(step, doesnt_appear, text):
    if world.LETTUCE_SELENIUM_CLIENT == 'saucelabs':
        multiplier = 2
    else:
        multiplier = 1
    if doesnt_appear:
        assert world.browser.is_text_not_present(text, wait_time=5 * multiplier)
    else:
        assert world.browser.is_text_present(text, wait_time=5 * multiplier)


@step('I am logged in$')
def i_am_logged_in(step):
    world.create_user('robot', 'test')
    world.log_in(username='robot', password='test')
    world.browser.visit(lettuce.django.django_url('/'))
    dash_css = 'section.container.dashboard'
    assert world.is_css_present(dash_css)


@step(u'I am an edX user$')
def i_am_an_edx_user(step):
    world.create_user('robot', 'test')


@step(u'User "([^"]*)" is an edX user$')
def registered_edx_user(step, uname):
    world.create_user(uname, 'test')


@step(u'All dialogs should be closed$')
def dialogs_are_closed(step):
    assert world.dialogs_closed()


@step(u'visit the url "([^"]*)"')
def visit_url(step, url):
    if 'COURSE' in world.scenario_dict:
        url = url.format(world.scenario_dict['COURSE'].id)
    world.browser.visit(lettuce.django.django_url(url))


@step(u'wait for AJAX to (?:finish|complete)')
def wait_ajax(_step):
    wait_for_ajax_complete()


@step('I will confirm all alerts')
def i_confirm_all_alerts(step):
    """
    Please note: This method must be called RIGHT BEFORE an expected alert
    Window variables are page local and thus all changes are removed upon navigating to a new page
    In addition, this method changes the functionality of ONLY future alerts
    """
    world.browser.execute_script('window.confirm = function(){return true;} ; window.alert = function(){return;}')


@step('I will cancel all alerts')
def i_cancel_all_alerts(step):
    """
    Please note: This method must be called RIGHT BEFORE an expected alert
    Window variables are page local and thus all changes are removed upon navigating to a new page
    In addition, this method changes the functionality of ONLY future alerts
    """
    world.browser.execute_script('window.confirm = function(){return false;} ; window.alert = function(){return;}')


@step('I will answer all prompts with "([^"]*)"')
def i_answer_prompts_with(step, prompt):
    """
    Please note: This method must be called RIGHT BEFORE an expected alert
    Window variables are page local and thus all changes are removed upon navigating to a new page
    In addition, this method changes the functionality of ONLY future alerts
    """
    world.browser.execute_script('window.prompt = function(){return %s;}') % prompt


@step('I run ipdb')
def run_ipdb(_step):
    """Run ipdb as step for easy debugging"""
    import ipdb
    ipdb.set_trace()
    assert True


@step(u'(I am viewing|s?he views) the course team settings$')
def view_course_team_settings(_step, whom):
    """ navigates to course team settings page """
    world.click_course_settings()
    link_css = 'li.nav-course-settings-team a'
    world.css_click(link_css)


@step('I get sudo access with password "([^"]*)"$')
def i_get_sudo_access(_step, password):
    """
    Get sudo access for instructor or staff user.
    Set the password value of the element to the specified password.
    Note that wait_for empty is due to password field
    It will return password like this **** not text.
    """
    if settings.FEATURES.get('ENABLE_DJANGO_SUDO', False):
        sudo_form = world.css_find('form.sudo-form')
        # check if sudo form is available then submit password to get sudo access
        # otherwise return True because sudo access already given.
        if len(sudo_form) > 0:
            css_selector = 'input[id=id_password]'
            world.retry_on_exception(lambda: world.css_find(css_selector)[0].fill(password))
            world.wait_for(lambda _: not world.css_has_value(css_selector, '', index=0))
            world.css_click('button[type=submit]')
        return True
