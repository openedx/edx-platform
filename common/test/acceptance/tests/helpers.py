"""
Test helper functions and base classes.
"""
from path import path
from bok_choy.web_app_test import WebAppTest
from bok_choy.promise import EmptyPromise


def wait_for_ajax(browser, try_limit=None, try_interval=0.5, timeout=60):
    """
    Make sure that all ajax requests are finished.
    :param try_limit (int or None): Number of attempts to make to satisfy the `Promise`. Can be `None` to
           disable the limit.
    :param try_interval (float): Number of seconds to wait between attempts.
    :param timeout (float): Maximum number of seconds to wait for the `Promise` to be satisfied before timing out.
    :param browser: selenium.webdriver, The Selenium-controlled browser that this page is loaded in.
    """
    def _is_ajax_finished():
        """
        Check if all the ajax call on current page completed.
        :return:
        """
        return browser.execute_script("return jQuery.active") == 0

    EmptyPromise(_is_ajax_finished, "Finished waiting for ajax requests.", try_limit=try_limit,
                 try_interval=try_interval, timeout=timeout).fulfill()


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
        self.course_info = {
            'org': 'test_org',
            'number': self.unique_id,
            'run': 'test_run',
            'display_name': 'Test Course' + self.unique_id
        }

        super(UniqueCourseTest, self).__init__(*args, **kwargs)

    @property
    def course_id(self):
        return self.COURSE_ID_SEPARATOR.join([
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        ])
