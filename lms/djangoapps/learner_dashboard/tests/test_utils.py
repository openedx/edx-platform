"""
Unit test module covering utils module
"""


import ddt
import six
from django.test import TestCase

from lms.djangoapps.learner_dashboard import utils


@ddt.ddt
class TestUtils(TestCase):
    """
    The test case class covering the all the utils functions
    """

    @ddt.data('path1/', '/path1/path2/', '/', '')
    def test_strip_course_id(self, path):
        """
        Test to make sure the function 'strip_course_id'
        handles various url input
        """
        actual = utils.strip_course_id(path + six.text_type(utils.FAKE_COURSE_KEY))
        self.assertEqual(actual, path)
