from django.conf import settings
from django.test import TestCase
from tempfile import NamedTemporaryFile
import os
from override_settings import override_settings

from status import get_site_status_msg

import xmodule.modulestore.django
from xmodule.modulestore.django import modulestore
from xmodule.modulestore import Location
from xmodule.modulestore.xml_importer import import_from_xml


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
        xmodule.modulestore.django._MODULESTORES = {}
        courses = modulestore().get_courses()

        def find_course(course_id):
            """Assumes the course is present"""
            return [c for c in courses if c.id==course_id][0]

        self.full = find_course("edX/full/6.002_Spring_2012")
        self.toy = find_course("edX/toy/2012_Fall")

    def create_status_file(self, contents):
        """
        Write contents to settings.STATUS_MESSAGE_PATH.
        """
        with open(settings.STATUS_MESSAGE_PATH, 'w') as f:
            f.write(contents)

    def remove_status_file(self):
        """Delete the status file if it exists"""
        if os.path.exists(settings.STATUS_MESSAGE_PATH):
            os.remove(settings.STATUS_MESSAGE_PATH)

    def tearDown(self):
        self.remove_status_file()

    def test_get_site_status_msg(self):
        """run the tests"""
        for (json_str, exp_none, exp_toy, exp_full) in self.checks:

            self.remove_status_file()
            if json_str:
                self.create_status_file(json_str)

            print "checking results for {0}".format(json_str)
            print "course=None:"
            self.assertEqual(get_site_status_msg(None), exp_none)
            print "course=toy:"
            self.assertEqual(get_site_status_msg(self.toy), exp_toy)
            print "course=full:"
            self.assertEqual(get_site_status_msg(self.full), exp_full)
