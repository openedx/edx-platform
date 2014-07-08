"""
Test helper functions and base classes.
"""
import json
import unittest
import functools
import requests
from path import path
from bok_choy.web_app_test import WebAppTest


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


class UniqueCourseTest(WebAppTest):
    """
    Test that provides a unique course ID.
    """

    COURSE_ID_SEPARATOR = "/"

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
        return self.COURSE_ID_SEPARATOR.join([
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        ])


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
    def get_configuartion(cls):
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
