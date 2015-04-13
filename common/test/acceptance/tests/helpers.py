"""
Test helper functions and base classes.
"""
import json
import unittest
import functools
import requests
import os
import time
from datetime import datetime
from path import path
from bok_choy.javascript import js_defined
from bok_choy.web_app_test import WebAppTest
from bok_choy.promise import EmptyPromise
from opaque_keys.edx.locator import CourseLocator
from pymongo import MongoClient
from xmodule.partitions.partitions import UserPartition
from xmodule.partitions.tests.test_partitions import MockUserPartitionScheme
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def skip_if_browser(browser):
    """
    Method decorator that skips a test if browser is `browser`

    Args:
        browser (str): name of internet browser

    Returns:
        Decorated function

    """
    def decorator(test_function):
        @functools.wraps(test_function)
        def wrapper(self, *args, **kwargs):
            if self.browser.name == browser:
                raise unittest.SkipTest('Skipping as this test will not work with {}'.format(browser))
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

    youtube_api_urls = {
        'main': 'https://www.youtube.com/',
        'player': 'http://www.youtube.com/iframe_api',
        'metadata': 'http://gdata.youtube.com/feeds/api/videos/',
        # For transcripts, you need to check an actual video, so we will
        # just specify our default video and see if that one is available.
        'transcript': 'http://video.google.com/timedtext?lang=en&v=3_yD_cEKoCk',
    }

    for url in youtube_api_urls.itervalues():
        try:
            response = requests.get(url, allow_redirects=False)
        except requests.exceptions.ConnectionError:
            return False

        if response.status_code >= 300:
            return False

    return True


def load_data_str(rel_path):
    """
    Load a file from the "data" directory as a string.
    `rel_path` is the path relative to the data directory.
    """
    full_path = path(__file__).abspath().dirname() / "data" / rel_path  # pylint: disable=no-value-for-parameter
    with open(full_path) as data_file:
        return data_file.read()


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
    page.browser.execute_script("""
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


def select_option_by_text(select_browser_query, option_text):
    """
    Chooses an option within a select by text (helper method for Select's select_by_visible_text method).
    """
    select = Select(select_browser_query.first.results[0])
    select.select_by_visible_text(option_text)


def get_selected_option_text(select_browser_query):
    """
    Returns the text value for the first selected option within a select.
    """
    select = Select(select_browser_query.first.results[0])
    return select.first_selected_option.text


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


def select_option_by_value(browser_query, value):
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
        # if value is not an option choice then it should return false
        if all_options_selected and not has_option:
            all_options_selected = False
        return all_options_selected

    # Make sure specified option is actually selected
    EmptyPromise(options_selected, "Option is selected").fulfill()


def is_option_value_selected(browser_query, value):
    """
    return true if given value is selected in html select element, else return false.
    """
    select = Select(browser_query.first.results[0])
    ddl_selected_value = select.first_selected_option.get_attribute('value')
    return ddl_selected_value == value


def element_has_text(page, css_selector, text):
    """
    Return true if the given text is present in the list.
    """
    text_present = False
    text_list = page.q(css=css_selector).text

    if len(text_list) > 0 and (text in text_list):
        text_present = True

    return text_present


def get_modal_alert(browser):
    """
    Returns instance of modal alert box shown in browser after waiting
    for 6 seconds
    """
    WebDriverWait(browser, 6).until(EC.alert_is_present())
    return browser.switch_to.alert


class EventsTestMixin(object):
    """
    Helpers and setup for running tests that evaluate events emitted
    """
    def setUp(self):
        super(EventsTestMixin, self).setUp()
        self.event_collection = MongoClient()["test"]["events"]
        self.event_collection.drop()
        self.browser_event_collection = MongoClient()["test"]["user_events"]
        self.browser_event_collection.drop()
        self.start_time = datetime.now()

    def reset_event_tracking(self):
        """
        Resets all event tracking so that previously captured events are removed.
        """
        self.event_collection.drop()
        self.browser_event_collection.drop()
        self.start_time = datetime.now()

    def assert_event_emitted_num_times(self, event_name, event_time, event_user_id, num_times_emitted):
        """
        Tests the number of times a particular event was emitted.
        :param event_name: Expected event name (e.g., "edx.course.enrollment.activated")
        :param event_time: Latest expected time, after which the event would fire (e.g., the beginning of the test case)
        :param event_user_id: user_id expected in the event
        :param num_times_emitted: number of times the event is expected to appear since the event_time
        """
        self.assertEqual(
            self.event_collection.find(
                {
                    "name": event_name,
                    "time": {"$gt": event_time},
                    "event.user_id": int(event_user_id),
                }
            ).count(), num_times_emitted
        )

    def get_matching_browser_events(self, event_type):
        """
        Returns a cursor for the matching browser events.
        """
        return self.browser_event_collection.find({
            "event_type": event_type,
            "time": {"$gt": self.start_time},
        })

    def verify_browser_events(self, event_type, expected_events):
        """Verify that the expected browser events were logged.
        Args:
            event_type (str): The type of event to be verified.
            expected_events (list): A list of dicts representing the events that should
                have been fired.
        """
        EmptyPromise(
            lambda: self.get_matching_browser_events(event_type).count() >= len(expected_events),
            "Waiting for enough browser events to be emitted"
        ).fulfill()

        # Verify that the correct number of events were found
        cursor = self.get_matching_browser_events(event_type)

        actual_events = []
        for i in range(0, cursor.count()):
            raw_event = cursor.next()
            actual_events.append(json.loads(raw_event["event"]))

        self.assertEqual(actual_events, expected_events)


class UniqueCourseTest(WebAppTest):
    """
    Test that provides a unique course ID.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a unique course ID.
        """
        super(UniqueCourseTest, self).__init__(*args, **kwargs)

    def setUp(self):
        super(UniqueCourseTest, self).setUp()

        self.course_info = {
            'org': 'test_org',
            'number': self.unique_id,
            'run': 'test_run',
            'display_name': 'Test Course' + self.unique_id
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
        return unicode(course_key)


class YouTubeConfigError(Exception):
    """
    Error occurred while configuring YouTube Stub Server.
    """
    pass


class YouTubeStubConfig(object):
    """
    Configure YouTube Stub Server.
    """

    PORT = 9080
    URL = 'http://127.0.0.1:{}/'.format(PORT)

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
                'YouTube Server Configuration Failed. URL {0}, Configuration Data: {1}, Status was {2}'.format(
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
                'YouTube Server Configuration Failed. URL: {0} Status was {1}'.format(
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
            return json.loads(response.content)
        else:
            return {}


def create_user_partition_json(partition_id, name, description, groups, scheme="random"):
    """
    Helper method to create user partition JSON. If scheme is not supplied, "random" is used.
    """
    return UserPartition(
        partition_id, name, description, groups, MockUserPartitionScheme(scheme)
    ).to_json()
