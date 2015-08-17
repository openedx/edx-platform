from django.conf import settings
from django.core.cache import cache
from django.test import TestCase
import os
from django.test.utils import override_settings
from tempfile import NamedTemporaryFile
import ddt

from .status import get_site_status_msg

# Get a name where we can put test files
TMP_FILE = NamedTemporaryFile(delete=False)
TMP_NAME = TMP_FILE.name
# Close it--we just want the path.
TMP_FILE.close()


@ddt.ddt
@override_settings(STATUS_MESSAGE_PATH=TMP_NAME)
class TestStatus(TestCase):
    """Test that the get_site_status_msg function does the right thing"""

    no_file = None

    invalid_json = """{
        "global" : "Hello, Globe",
        }"""

    global_only = """{
        "global" : "Hello, Globe"
        }"""

    toy_only = """{
        "edX/toy/2012_Fall" : "A toy story"
        }"""

    global_and_toy = """{
        "global" : "Hello, Globe",
        "edX/toy/2012_Fall" : "A toy story"
        }"""

    # json to use, expected results for course=None (e.g. homepage),
    # for toy course, for full course.  Note that get_site_status_msg
    # is supposed to return global message even if course=None.  The
    # template just happens to not display it outside the courseware
    # at the moment...
    checks = [
        (no_file, None, None, None),
        (invalid_json, None, None, None),
        (global_only, "Hello, Globe", "Hello, Globe", "Hello, Globe"),
        (toy_only, None, "A toy story", None),
        (global_and_toy, "Hello, Globe", "Hello, Globe<br>A toy story", "Hello, Globe"),
    ]

    def setUp(self):
        """
        Fake course ids, since we don't have to have full django
        settings (common tests run without the lms settings imported)
        """
        super(TestStatus, self).setUp()
        self.full_id = 'edX/full/2012_Fall'
        self.toy_id = 'edX/toy/2012_Fall'
        self.addCleanup(self.remove_status_file)

    def create_status_file(self, contents):
        """
        Write contents to settings.STATUS_MESSAGE_PATH.
        """
        with open(settings.STATUS_MESSAGE_PATH, 'w') as f:
            f.write(contents)

    def clear_status_cache(self):
        """
        Remove the cached status message, if found
        """
        if cache.get('site_status_msg') is not None:
            cache.delete('site_status_msg')

    def remove_status_file(self):
        """Delete the status file if it exists"""
        if os.path.exists(settings.STATUS_MESSAGE_PATH):
            os.remove(settings.STATUS_MESSAGE_PATH)

    @ddt.data(*checks)
    @ddt.unpack
    def test_get_site_status_msg(self, json_str, exp_none, exp_toy, exp_full):
        """run the tests"""

        self.remove_status_file()
        if json_str:
            self.create_status_file(json_str)

        for course_id, expected_msg in [(None, exp_none), (self.toy_id, exp_toy), (self.full_id, exp_full)]:
            self.assertEqual(get_site_status_msg(course_id), expected_msg)
            self.assertEqual(cache.get('site_status_msg'), expected_msg)
            # check that `get_site_status_msg` works as expected when the cache
            # is warmed, too
            self.assertEqual(get_site_status_msg(course_id), expected_msg)
            self.clear_status_cache()
