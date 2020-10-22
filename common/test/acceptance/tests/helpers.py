"""
Test helper functions and base classes.
"""

import functools
import inspect
import io
import json
import operator
import os
import pprint
import sys
import urlparse
from contextlib import contextmanager
from datetime import datetime
from unittest import SkipTest, TestCase

import requests
from bok_choy.javascript import js_defined
from bok_choy.page_object import XSS_INJECTION
from bok_choy.promise import EmptyPromise, Promise
from bok_choy.web_app_test import WebAppTest
from opaque_keys.edx.locator import CourseLocator
from path import Path as path
from pymongo import ASCENDING, MongoClient
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait

from capa.tests.response_xml_factory import MultipleChoiceResponseXMLFactory
from common.test.acceptance.fixtures.course import XBlockFixtureDesc
from common.test.acceptance.pages.common import BASE_URL
from common.test.acceptance.pages.common.auto_auth import AutoAuthPage
from openedx.core.lib.tests.assertions.events import EventMatchTolerates, assert_event_matches, is_matching_event
from openedx.core.release import RELEASE_LINE, doc_version
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
                raise SkipTest('Skipping as this test will not work with {}'.format(browser))
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

    for url in youtube_api_urls.itervalues():
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
    return browser.execute_script("return $('{}').is(':focus')".format(selector))


def load_data_str(rel_path):
    """
    Load a file from the "data" directory as a string.
    `rel_path` is the path relative to the data directory.
    """
    full_path = path(__file__).abspath().dirname() / "data" / rel_path  # pylint: disable=no-value-for-parameter
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

    msg = 'Selected option {}'.format(option_text)
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

    if text_list and (text in text_list):
        text_present = True

    return text_present


def get_modal_alert(browser):
    """
    Returns instance of modal alert box shown in browser after waiting
    for 6 seconds
    """
    WebDriverWait(browser, 6).until(EC.alert_is_present())
    return browser.switch_to.alert


def get_element_padding(page, selector):
    """
    Get Padding of the element with given selector,

    :returns a dict object with the following keys.
            1 - padding-top
            2 - padding-right
            3 - padding-bottom
            4 - padding-left

    Example Use:
        progress_page.get_element_padding('.wrapper-msg.wrapper-auto-cert')

    """
    js_script = """
        var $element = $('%(selector)s');

        element_padding = {
            'padding-top': $element.css('padding-top').replace("px", ""),
            'padding-right': $element.css('padding-right').replace("px", ""),
            'padding-bottom': $element.css('padding-bottom').replace("px", ""),
            'padding-left': $element.css('padding-left').replace("px", "")
        };

        return element_padding;
    """ % {'selector': selector}

    return page.browser.execute_script(js_script)


def is_404_page(browser):
    """ Check if page is 404 """
    return 'Page not found (404)' in browser.find_element_by_tag_name('h1').text


def create_multiple_choice_xml(correct_choice=2, num_choices=4):
    """
    Return the Multiple Choice Problem XML, given the name of the problem.
    """
    # all choices are incorrect except for correct_choice
    choices = [False for _ in range(num_choices)]
    choices[correct_choice] = True

    choice_names = ['choice_{}'.format(index) for index in range(num_choices)]
    question_text = 'The correct answer is Choice {}'.format(correct_choice)

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


def auto_auth(browser, username, email, staff, course_id):
    """
    Logout and login with given credentials.
    """
    AutoAuthPage(browser, username=username, email=email, course_id=course_id, staff=staff).visit()


def assert_link(test, expected_link, actual_link):
    """
    Assert that 'href' and text inside help DOM element are correct.

    Arguments:
        test: Test on which links are being tested.
        expected_link (dict): The expected link attributes.
        actual_link (dict): The actual link attribute on page.
    """
    test.assertEqual(expected_link['href'], actual_link.get_attribute('href'))
    test.assertEqual(expected_link['text'], actual_link.text)


def assert_opened_help_link_is_correct(test, url):
    """
    Asserts that url of browser when help link is clicked is correct.
    Arguments:
        test (AcceptanceTest): test calling this method.
        url (str): url to verify.
    """
    test.browser.switch_to_window(test.browser.window_handles[-1])
    WebDriverWait(test.browser, 10).until(lambda driver: driver.current_url == url)
    # Check that the URL loads. Can't do this in the browser because it might
    # be loading a "Maze Found" missing content page.
    response = requests.get(url)
    test.assertEqual(response.status_code, 200, "URL {!r} returned {}".format(url, response.status_code))


EDX_BOOKS = {
    'course_author': 'edx-partner-course-staff',
    'learner': 'edx-guide-for-students',
}

OPEN_BOOKS = {
    'course_author': 'open-edx-building-and-running-a-course',
    'learner': 'open-edx-learner-guide',
}


def url_for_help(book_slug, path_component):
    """
    Create a full help URL given a book slug and a path component.
    """
    # Emulate the switch between books that happens in envs/bokchoy.py
    books = EDX_BOOKS if RELEASE_LINE == "master" else OPEN_BOOKS
    url = 'https://edx.readthedocs.io/projects/{}/en/{}{}'.format(books[book_slug], doc_version(), path_component)
    return url


class EventsTestMixin(TestCase):
    """
    Helpers and setup for running tests that evaluate events emitted
    """
    def setUp(self):
        super(EventsTestMixin, self).setUp()
        mongo_host = 'edx.devstack.mongo' if 'BOK_CHOY_HOSTNAME' in os.environ else 'localhost'
        self.event_collection = MongoClient(mongo_host)["test"]["events"]
        self.start_time = datetime.now()

    def reset_event_tracking(self):
        """Drop any events that have been collected thus far and start collecting again from scratch."""
        self.event_collection.drop()
        self.start_time = datetime.now()

    @contextmanager
    def capture_events(self, event_filter=None, number_of_matches=1, captured_events=None):
        """
        Context manager that captures all events emitted while executing a particular block.

        All captured events are stored in the list referenced by `captured_events`. Note that this list is appended to
        *in place*. The events will be appended to the list in the order they are emitted.

        The `event_filter` is expected to be a callable that allows you to filter the event stream and select particular
        events of interest. A dictionary `event_filter` is also supported, which simply indicates that the event should
        match that provided expectation.

        `number_of_matches` tells this context manager when enough events have been found and it can move on. The
        context manager will not exit until this many events have passed the filter. If not enough events are found
        before a timeout expires, then this will raise a `BrokenPromise` error. Note that this simply states that
        *at least* this many events have been emitted, so `number_of_matches` is simply a lower bound for the size of
        `captured_events`.
        """
        start_time = datetime.utcnow()

        yield

        events = self.wait_for_events(
            start_time=start_time, event_filter=event_filter, number_of_matches=number_of_matches)

        if captured_events is not None and hasattr(captured_events, 'append') and callable(captured_events.append):
            for event in events:
                captured_events.append(event)

    @contextmanager
    def assert_events_match_during(self, event_filter=None, expected_events=None, in_order=True):
        """
        Context manager that ensures that events matching the `event_filter` and `expected_events` are emitted.

        This context manager will filter out the event stream using the `event_filter` and wait for
        `len(expected_events)` to match the filter.

        It will then compare the events in order with their counterpart in `expected_events` to ensure they match the
        more detailed assertion.

        Typically `event_filter` will be an `event_type` filter and the `expected_events` list will contain more
        detailed assertions.
        """
        captured_events = []
        with self.capture_events(event_filter, len(expected_events), captured_events):
            yield

        self.assert_events_match(expected_events, captured_events, in_order=in_order)

    def wait_for_events(self, start_time=None, event_filter=None, number_of_matches=1, timeout=None):
        """
        Wait for `number_of_matches` events to pass the `event_filter`.

        By default, this will look at all events that have been emitted since the beginning of the setup of this mixin.
        A custom `start_time` can be specified which will limit the events searched to only those emitted after that
        time.

        The `event_filter` is expected to be a callable that allows you to filter the event stream and select particular
        events of interest. A dictionary `event_filter` is also supported, which simply indicates that the event should
        match that provided expectation.

        `number_of_matches` lets us know when enough events have been found and it can move on. The function will not
        return until this many events have passed the filter. If not enough events are found before a timeout expires,
        then this will raise a `BrokenPromise` error. Note that this simply states that *at least* this many events have
        been emitted, so `number_of_matches` is simply a lower bound for the size of `captured_events`.

        Specifying a custom `timeout` can allow you to extend the default 30 second timeout if necessary.
        """
        if start_time is None:
            start_time = self.start_time

        if timeout is None:
            timeout = 30

        def check_for_matching_events():
            """Gather any events that have been emitted since `start_time`"""
            return self.matching_events_were_emitted(
                start_time=start_time,
                event_filter=event_filter,
                number_of_matches=number_of_matches
            )

        return Promise(
            check_for_matching_events,
            # This is a bit of a hack, Promise calls str(description), so I set the description to an object with a
            # custom __str__ and have it do some intelligent stuff to generate a helpful error message.
            CollectedEventsDescription(
                'Waiting for {number_of_matches} events to match the filter:\n{event_filter}'.format(
                    number_of_matches=number_of_matches,
                    event_filter=self.event_filter_to_descriptive_string(event_filter),
                ),
                functools.partial(self.get_matching_events_from_time, start_time=start_time, event_filter={})
            ),
            timeout=timeout
        ).fulfill()

    def matching_events_were_emitted(self, start_time=None, event_filter=None, number_of_matches=1):
        """Return True if enough events have been emitted that pass the `event_filter` since `start_time`."""
        matching_events = self.get_matching_events_from_time(start_time=start_time, event_filter=event_filter)
        return len(matching_events) >= number_of_matches, matching_events

    def get_matching_events_from_time(self, start_time=None, event_filter=None):
        """
        Return a list of events that pass the `event_filter` and were emitted after `start_time`.

        This function is used internally by most of the other assertions and convenience methods in this class.

        The `event_filter` is expected to be a callable that allows you to filter the event stream and select particular
        events of interest. A dictionary `event_filter` is also supported, which simply indicates that the event should
        match that provided expectation.
        """
        if start_time is None:
            start_time = self.start_time

        if isinstance(event_filter, dict):
            event_filter = functools.partial(is_matching_event, event_filter)
        elif not callable(event_filter):
            raise ValueError(
                'event_filter must either be a dict or a callable function with as single "event" parameter that '
                'returns a boolean value.'
            )

        matching_events = []
        cursor = self.event_collection.find(
            {
                "time": {
                    "$gte": start_time
                }
            }
        ).sort("time", ASCENDING)
        for event in cursor:
            matches = False
            try:
                # Mongo automatically assigns an _id to all events inserted into it. We strip it out here, since
                # we don't care about it.
                del event['_id']
                if event_filter is not None:
                    # Typically we will be grabbing all events of a particular type, however, you can use arbitrary
                    # logic to identify the events that are of interest.
                    matches = event_filter(event)
            except AssertionError:
                # allow the filters to use "assert" to filter out events
                continue
            else:
                if matches is None or matches:
                    matching_events.append(event)
        return matching_events

    def assert_matching_events_were_emitted(self, start_time=None, event_filter=None, number_of_matches=1):
        """Assert that at least `number_of_matches` events have passed the filter since `start_time`."""
        description = CollectedEventsDescription(
            'Not enough events match the filter:\n' + self.event_filter_to_descriptive_string(event_filter),
            functools.partial(self.get_matching_events_from_time, start_time=start_time, event_filter={})
        )

        self.assertTrue(
            self.matching_events_were_emitted(
                start_time=start_time, event_filter=event_filter, number_of_matches=number_of_matches
            ),
            description
        )

    def assert_no_matching_events_were_emitted(self, event_filter, start_time=None):
        """Assert that no events have passed the filter since `start_time`."""
        matching_events = self.get_matching_events_from_time(start_time=start_time, event_filter=event_filter)

        description = CollectedEventsDescription(
            'Events unexpected matched the filter:\n' + self.event_filter_to_descriptive_string(event_filter),
            lambda: matching_events
        )

        self.assertEquals(len(matching_events), 0, description)

    def assert_events_match(self, expected_events, actual_events, in_order=True):
        """Assert that each actual event matches one of the expected events.

        Args:
            expected_events (List): a list of dicts representing the expected events.
            actual_events (List): a list of dicts that were actually recorded.
            in_order (bool): if True then the events must be in the same order (defaults to True).
        """
        if in_order:
            for expected_event, actual_event in zip(expected_events, actual_events):
                assert_event_matches(
                    expected_event,
                    actual_event,
                    tolerate=EventMatchTolerates.lenient()
                )
        else:
            for expected_event in expected_events:
                actual_event = next(event for event in actual_events if is_matching_event(expected_event, event))
                assert_event_matches(
                    expected_event,
                    actual_event or {},
                    tolerate=EventMatchTolerates.lenient()
                )

    def relative_path_to_absolute_uri(self, relative_path):
        """Return an aboslute URI given a relative path taking into account the test context."""
        return urlparse.urljoin(BASE_URL, relative_path)

    def event_filter_to_descriptive_string(self, event_filter):
        """Find the source code of the callable or pretty-print the dictionary"""
        message = ''
        if callable(event_filter):
            file_name = '(unknown)'
            try:
                file_name = inspect.getsourcefile(event_filter)
            except TypeError:
                pass

            try:
                list_of_source_lines, line_no = inspect.getsourcelines(event_filter)
            except IOError:
                pass
            else:
                message = '{file_name}:{line_no}\n{hr}\n{event_filter}\n{hr}'.format(
                    event_filter=''.join(list_of_source_lines).rstrip(),
                    file_name=file_name,
                    line_no=line_no,
                    hr='-' * 20,
                )

        if not message:
            message = '{hr}\n{event_filter}\n{hr}'.format(
                event_filter=pprint.pformat(event_filter),
                hr='-' * 20,
            )

        return message


class CollectedEventsDescription(object):
    """
    Produce a clear error message when tests fail.

    This class calls the provided `get_events_func` when converted to a string, and pretty prints the returned events.
    """

    def __init__(self, description, get_events_func):
        self.description = description
        self.get_events_func = get_events_func

    def __str__(self):
        message_lines = [
            self.description,
            'Events:'
        ]
        events = self.get_events_func()
        events.sort(key=operator.itemgetter('time'), reverse=True)
        for event in events[:MAX_EVENTS_IN_FAILURE_OUTPUT]:
            message_lines.append(pprint.pformat(event))
        if len(events) > MAX_EVENTS_IN_FAILURE_OUTPUT:
            message_lines.append(
                'Too many events to display, the remaining events were omitted. Run locally to diagnose.')

        return '\n\n'.join(message_lines)


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


def assert_nav_help_link(test, page, href, signed_in=True, close_window=True):
    """
    Asserts that help link in navigation bar is correct.

    It first checks the url inside anchor DOM element and
    then clicks to ensure that help opens correctly.

    Arguments:
    test (AcceptanceTest): Test object
    page (PageObject): Page object to perform tests on.
    href (str): The help link which we expect to see when it is opened.
    signed_in (bool): Specifies whether user is logged in or not. (It affects the css)
    close_window(bool): Close the newly-opened help window before continuing
    """
    expected_link = {
        'href': href,
        'text': 'Help'
    }
    # Get actual anchor help element from the page.
    actual_link = page.get_nav_help_element_and_click_help(signed_in)
    # Assert that 'href' and text are the same as expected.
    assert_link(test, expected_link, actual_link)
    # Assert that opened link is correct
    assert_opened_help_link_is_correct(test, href)
    # Close the help window if not kept open intentionally
    if close_window:
        close_help_window(page)


def assert_side_bar_help_link(test, page, href, help_text, as_list_item=False, index=-1, close_window=True):
    """
    Asserts that help link in side bar is correct.

    It first checks the url inside anchor DOM element and
    then clicks to ensure that help opens correctly.

    Arguments:
    test (AcceptanceTest): Test object
    page (PageObject): Page object to perform tests on.
    href (str): The help link which we expect to see when it is opened.
    as_list_item (bool): Specifies whether help element is in one of the
                         'li' inside a sidebar list DOM element.
    index (int): The index of element in case there are more than
                 one matching elements.
    close_window(bool): Close the newly-opened help window before continuing
    """
    expected_link = {
        'href': href,
        'text': help_text
    }
    # Get actual anchor help element from the page.
    actual_link = page.get_side_bar_help_element_and_click_help(as_list_item=as_list_item, index=index)
    # Assert that 'href' and text are the same as expected.
    assert_link(test, expected_link, actual_link)
    # Assert that opened link is correct
    assert_opened_help_link_is_correct(test, href)
    # Close the help window if not kept open intentionally
    if close_window:
        close_help_window(page)


def close_help_window(page):
    """
    Closes the help window
    Args:
        page (PageObject): Page object to perform tests on.
    """
    browser_url = page.browser.current_url
    if browser_url.startswith('https://edx.readthedocs.io') or browser_url.startswith('http://edx.readthedocs.io'):
        page.browser.close()  # close only the current window
        page.browser.switch_to_window(page.browser.window_handles[0])


class TestWithSearchIndexMixin(object):
    """ Mixin encapsulating search index creation """
    TEST_INDEX_FILENAME = "test_root/index_file.dat"

    def _create_search_index(self):
        """ Creates search index backing file """
        with open(self.TEST_INDEX_FILENAME, "w+") as index_file:
            json.dump({}, index_file)

    def _cleanup_index_file(self):
        """ Removes search index backing file """
        remove_file(self.TEST_INDEX_FILENAME)
