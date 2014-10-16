"""
Test helper functions and base classes.
"""
import json
import unittest
import functools
import requests
import os
from path import path
from bok_choy.web_app_test import WebAppTest
from opaque_keys.edx.locator import CourseLocator


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
        'transcript': 'http://video.google.com/timedtext?lang=en&v=OEoXaMPEzfM',
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
    full_path = path(__file__).abspath().dirname() / "data" / rel_path  # pylint: disable=E1120
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


def disable_jquery_animations(page):
    """
    Disable jQuery animations.
    """
    page.browser.execute_script("jQuery.fx.off = true;")


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
