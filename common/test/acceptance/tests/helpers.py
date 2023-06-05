"""
Test helper functions and base classes.
"""


import functools
import io
import json
import os
import sys
from datetime import datetime
from unittest import SkipTest, TestCase

import requests
import six
from bok_choy.javascript import js_defined
from bok_choy.page_object import XSS_INJECTION
from bok_choy.promise import EmptyPromise, Promise
from bok_choy.web_app_test import WebAppTest
from opaque_keys.edx.locator import CourseLocator
from path import Path as path
from pymongo import ASCENDING, MongoClient
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait
from six.moves import range, zip

from capa.tests.response_xml_factory import MultipleChoiceResponseXMLFactory
from common.test.acceptance.fixtures.course import XBlockFixtureDesc
from common.test.acceptance.pages.common.auto_auth import AutoAuthPage
from xmodule.partitions.partitions import UserPartition

MAX_EVENTS_IN_FAILURE_OUTPUT = 20


def skip_if_browser(browser):
    """
    Method decorator that skips a test if browser is `browser`

    Args:
        browser (str): name of internet browser

    Returns:
        Decorated function

    """
    def decorator(test_function):
        """
        The decorator to be applied to the test function.
        """
        @functools.wraps(test_function)
        def wrapper(self, *args, **kwargs):
            if self.browser.name == browser:
                raise SkipTest(u'Skipping as this test will not work with {}'.format(browser))
            test_function(self, *args, **kwargs)
        return wrapper
    return decorator


def is_youtube_available():
    """
    Check if the required youtube urls are available.

    If a URL in `youtube_api_urls` is not reachable then subsequent URLs will not be checked.

    Returns:
        bool:

    """
    # TODO: Design and implement a better solution that is reliable and repeatable,
    # reflects how the application works in production, and limits the third-party
    # network traffic (e.g. repeatedly retrieving the js from youtube from the browser).

    youtube_api_urls = {
        'main': 'https://www.youtube.com/',
        'player': 'https://www.youtube.com/iframe_api',
        # For transcripts, you need to check an actual video, so we will
        # just specify our default video and see if that one is available.
        'transcript': 'http://video.google.com/timedtext?lang=en&v=3_yD_cEKoCk',
    }

    for url in six.itervalues(youtube_api_urls):
        try:
            response = requests.get(url, allow_redirects=False)
        except requests.exceptions.ConnectionError:
            return False

        if response.status_code >= 300:
            return False

    return True


def is_focused_on_element(browser, selector):
    """
    Check if the focus is on the element that matches the selector.
    """
    return browser.execute_script(u"return $('{}').is(':focus')".format(selector))


def load_data_str(rel_path):
    """
    Load a file from the "data" directory as a string.
    `rel_path` is the path relative to the data directory.
    """
    full_path = path(__file__).abspath().dirname() / "data" / rel_path
    with open(full_path) as data_file:
        return data_file.read()


def remove_file(filename):
    """
    Remove a file if it exists
    """
    if os.path.exists(filename):
        os.remove(filename)


def disable_animations(page):
    """
    Disable jQuery and CSS3 animations.
    """
    disable_jquery_animations(page)
    disable_css_animations(page)


def enable_animations(page):
    """
    Enable jQuery and CSS3 animations.
    """
    enable_jquery_animations(page)
    enable_css_animations(page)


@js_defined('window.jQuery')
def disable_jquery_animations(page):
    """
    Disable jQuery animations.
    """
    page.browser.execute_script("jQuery.fx.off = true;")


@js_defined('window.jQuery')
def enable_jquery_animations(page):
    """
    Enable jQuery animations.
    """
    page.browser.execute_script("jQuery.fx.off = false;")


def disable_css_animations(page):
    """
    Disable CSS3 animations, transitions, transforms.
    """
    page.browser.execute_script(u"""
        var id = 'no-transitions';

        // if styles were already added, just do nothing.
        if (document.getElementById(id)) {
            return;
        }

        var css = [
                '* {',
                    '-webkit-transition: none !important;',
                    '-moz-transition: none !important;',
                    '-o-transition: none !important;',
                    '-ms-transition: none !important;',
                    'transition: none !important;',
                    '-webkit-transition-property: none !important;',
                    '-moz-transition-property: none !important;',
                    '-o-transition-property: none !important;',
                    '-ms-transition-property: none !important;',
                    'transition-property: none !important;',
                    '-webkit-transform: none !important;',
                    '-moz-transform: none !important;',
                    '-o-transform: none !important;',
                    '-ms-transform: none !important;',
                    'transform: none !important;',
                    '-webkit-animation: none !important;',
                    '-moz-animation: none !important;',
                    '-o-animation: none !important;',
                    '-ms-animation: none !important;',
                    'animation: none !important;',
                '}'
            ].join(''),
            head = document.head || document.getElementsByTagName('head')[0],
            styles = document.createElement('style');

        styles.id = id;
        styles.type = 'text/css';
        if (styles.styleSheet){
          styles.styleSheet.cssText = css;
        } else {
          styles.appendChild(document.createTextNode(css));
        }

        head.appendChild(styles);
    """)


def enable_css_animations(page):
    """
    Enable CSS3 animations, transitions, transforms.
    """
    page.browser.execute_script("""
        var styles = document.getElementById('no-transitions'),
            head = document.head || document.getElementsByTagName('head')[0];

        head.removeChild(styles)
    """)


def select_option_by_text(select_browser_query, option_text, focus_out=False):
    """
    Chooses an option within a select by text (helper method for Select's select_by_visible_text method).

    Wrap this in a Promise to prevent a StaleElementReferenceException
    from being raised while the DOM is still being rewritten
    """
    def select_option(query, value):
        """ Get the first select element that matches the query and select the desired value. """
        try:
            select = Select(query.first.results[0])
            select.select_by_visible_text(value)
            if focus_out:
                query.first.results[0].send_keys(Keys.TAB)
            return True
        except StaleElementReferenceException:
            return False

    msg = u'Selected option {}'.format(option_text)
    EmptyPromise(lambda: select_option(select_browser_query, option_text), msg).fulfill()


def get_selected_option_text(select_browser_query):
    """
    Returns the text value for the first selected option within a select.

    Wrap this in a Promise to prevent a StaleElementReferenceException
    from being raised while the DOM is still being rewritten
    """
    def get_option(query):
        """ Get the first select element that matches the query and return its value. """
        try:
            select = Select(query.first.results[0])
            return (True, select.first_selected_option.text)
        except StaleElementReferenceException:
            return (False, None)

    text = Promise(lambda: get_option(select_browser_query), 'Retrieved selected option text').fulfill()
    return text


def get_options(select_browser_query):
    """
    Returns all the options for the given select.
    """
    return Select(select_browser_query.first.results[0]).options


def generate_course_key(org, number, run):
    """
    Makes a CourseLocator from org, number and run
    """
    default_store = os.environ.get('DEFAULT_STORE', 'draft')
    return CourseLocator(org, number, run, deprecated=(default_store == 'draft'))


def select_option_by_value(browser_query, value, focus_out=False):
    """
    Selects a html select element by matching value attribute
    """
    select = Select(browser_query.first.results[0])
    select.select_by_value(value)

    def options_selected():
        """
        Returns True if all options in select element where value attribute
        matches `value`. if any option is not selected then returns False
        and select it. if value is not an option choice then it returns False.
        """
        all_options_selected = True
        has_option = False
        for opt in select.options:
            if opt.get_attribute('value') == value:
                has_option = True
                if not opt.is_selected():
                    all_options_selected = False
                    opt.click()
        if all_options_selected and not has_option:
            all_options_selected = False
        if focus_out:
            browser_query.first.results[0].send_keys(Keys.TAB)
        return all_options_selected

    # Make sure specified option is actually selected
    EmptyPromise(options_selected, "Option is selected").fulfill()


def create_multiple_choice_xml(correct_choice=2, num_choices=4):
    """
    Return the Multiple Choice Problem XML, given the name of the problem.
    """
    # all choices are incorrect except for correct_choice
    choices = [False for _ in range(num_choices)]
    choices[correct_choice] = True

    choice_names = ['choice_{}'.format(index) for index in range(num_choices)]
    question_text = u'The correct answer is Choice {}'.format(correct_choice)

    return MultipleChoiceResponseXMLFactory().build_xml(
        question_text=question_text,
        choices=choices,
        choice_names=choice_names,
    )


def create_multiple_choice_problem(problem_name):
    """
    Return the Multiple Choice Problem Descriptor, given the name of the problem.
    """
    xml_data = create_multiple_choice_xml()
    return XBlockFixtureDesc(
        'problem',
        problem_name,
        data=xml_data,
        metadata={'rerandomize': 'always'}
    )


def auto_auth(browser, username, email, staff, course_id, **kwargs):
    """
    Logout and login with given credentials.
    """
    AutoAuthPage(browser, username=username, email=email, course_id=course_id, staff=staff, **kwargs).visit()


class EventsTestMixin(TestCase):
    """
    Helpers and setup for running tests that evaluate events emitted
    """
    def setUp(self):
        super(EventsTestMixin, self).setUp()
        mongo_host = 'edx.devstack.mongo' if 'BOK_CHOY_HOSTNAME' in os.environ else 'localhost'
        self.event_collection = MongoClient(mongo_host)["test"]["events"]
        self.start_time = datetime.now()


class AcceptanceTest(WebAppTest):
    """
    The base class of all acceptance tests.
    """

    def __init__(self, *args, **kwargs):
        super(AcceptanceTest, self).__init__(*args, **kwargs)

        # Use long messages so that failures show actual and expected values
        self.longMessage = True  # pylint: disable=invalid-name

    def tearDown(self):
        self._save_console_log()
        super(AcceptanceTest, self).tearDown()

    def _save_console_log(self):
        """
        Retrieve any JS errors caught by our error handler in the browser
        and save them to a log file.  This is a workaround for Firefox not
        supporting the Selenium log capture API yet; for details, see
        https://github.com/mozilla/geckodriver/issues/284
        """
        browser_name = os.environ.get('SELENIUM_BROWSER', 'firefox')
        if browser_name != 'firefox':
            return
        result = sys.exc_info()
        exception_type = result[0]

        # Do not save for skipped tests.
        if exception_type is SkipTest:
            return

        # If the test failed, save the browser console log.
        # The exception info will either be an assertion error (on failure)
        # or an actual exception (on error)
        if result != (None, None, None):
            logs = self.browser.execute_script("return window.localStorage.getItem('console_log_capture');")
            if not logs:
                return
            logs = json.loads(logs)

            log_dir = os.environ.get('SELENIUM_DRIVER_LOG_DIR')
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)

            log_path = os.path.join(log_dir, '{}_browser.log'.format(self.id()))
            with io.open(log_path, 'w') as browser_log:
                for (message, url, line_no, col_no, stack) in logs:
                    browser_log.write(u"{}:{}:{}: {}\n    {}\n".format(
                        url,
                        line_no,
                        col_no,
                        message,
                        (stack or "").replace('\n', '\n    ')
                    ))


class UniqueCourseTest(AcceptanceTest):
    """
    Test that provides a unique course ID.
    """

    def setUp(self):
        super(UniqueCourseTest, self).setUp()

        self.course_info = {
            'org': 'test_org',
            'number': self.unique_id,
            'run': 'test_run',
            'display_name': 'Test Course' + XSS_INJECTION + self.unique_id
        }

    @property
    def course_id(self):
        """
        Returns the serialized course_key for the test
        """
        # TODO - is there a better way to make this agnostic to the underlying default module store?
        default_store = os.environ.get('DEFAULT_STORE', 'draft')
        course_key = CourseLocator(
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run'],
            deprecated=(default_store == 'draft')
        )
        return six.text_type(course_key)


class YouTubeConfigError(Exception):
    """
    Error occurred while configuring YouTube Stub Server.
    """
    pass


class YouTubeStubConfig(object):
    """
    Configure YouTube Stub Server.
    """

    YOUTUBE_HOSTNAME = os.environ.get('BOK_CHOY_HOSTNAME', '127.0.0.1')
    PORT = 9080
    URL = 'http://{}:{}/'.format(YOUTUBE_HOSTNAME, PORT)

    @classmethod
    def configure(cls, config):
        """
        Allow callers to configure the stub server using the /set_config URL.

        Arguments:
            config (dict): Configuration dictionary.

        Raises:
            YouTubeConfigError

        """
        youtube_stub_config_url = cls.URL + 'set_config'

        config_data = {param: json.dumps(value) for param, value in config.items()}
        response = requests.put(youtube_stub_config_url, data=config_data)

        if not response.ok:
            raise YouTubeConfigError(
                u'YouTube Server Configuration Failed. URL {0}, Configuration Data: {1}, Status was {2}'.format(
                    youtube_stub_config_url, config, response.status_code))

    @classmethod
    def reset(cls):
        """
        Reset YouTube Stub Server Configurations using the /del_config URL.

        Raises:
            YouTubeConfigError

        """
        youtube_stub_config_url = cls.URL + 'del_config'

        response = requests.delete(youtube_stub_config_url)

        if not response.ok:
            raise YouTubeConfigError(
                u'YouTube Server Configuration Failed. URL: {0} Status was {1}'.format(
                    youtube_stub_config_url, response.status_code))

    @classmethod
    def get_configuration(cls):
        """
        Allow callers to get current stub server configuration.

        Returns:
            dict

        """
        youtube_stub_config_url = cls.URL + 'get_config'

        response = requests.get(youtube_stub_config_url)

        if response.ok:
            return json.loads(response.content.decode('utf-8'))
        else:
            return {}


def click_and_wait_for_window(page, element):
    """
    To avoid a race condition, click an element that launces a new window, and
    wait for that window to launch.
    To check this, make sure the number of window_handles increases by one.

    Arguments:
    page (PageObject): Page object to perform method on
    element (WebElement): Clickable element that triggers the new window to open
    """
    num_windows = len(page.browser.window_handles)
    element.click()
    WebDriverWait(page.browser, 10).until(
        lambda driver: len(driver.window_handles) > num_windows
    )


def create_user_partition_json(partition_id, name, description, groups, scheme="random"):
    """
    Helper method to create user partition JSON. If scheme is not supplied, "random" is used.
    """
    # All that is persisted about a scheme is its name.
    class MockScheme(object):
        name = scheme

    return UserPartition(
        partition_id, name, description, groups, MockScheme()
    ).to_json()
