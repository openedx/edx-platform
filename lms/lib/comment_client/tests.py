""" Unit tests for comment_client package"""

import ddt
import mock
from datetime import datetime
from django.test import TestCase

from opaque_keys.edx.locator import CourseLocator
from lms.lib.comment_client import User, CommentClientRequestError
from lms.lib.comment_client.user import get_user_social_stats

TEST_ORG = 'test_org'
TEST_COURSE_ID = 'test_id'
TEST_RUN = 'test_run'


@ddt.ddt
class UserTests(TestCase):
    """ Tests for User model """
    @ddt.unpack
    @ddt.data(
        (CourseLocator(TEST_ORG, TEST_COURSE_ID, TEST_RUN), None, None, {}),
        (CourseLocator(TEST_ORG, TEST_COURSE_ID, TEST_RUN), datetime(2015, 01, 01), None, {'1': 1}),
        (CourseLocator("edX", "DemoX", "now"), datetime(2014, 12, 03, 18, 15, 44), None, {'1': {'num_threads': 10}}),
        (CourseLocator("edX", "DemoX", "now"), datetime(2016, 03, 17, 22, 54, 03), 'discussion', {}),
        (CourseLocator("Umbrella", "ZMB101", "T1"), datetime(2016, 03, 17, 22, 54, 03), 'question', {'num_threads': 5}),
    )
    def test_all_social_stats_sends_correct_request(self, course_key, end_date, thread_type, expected_result):
        """
        Tests that all_social_stats classmethod invokes get_user_social_stats with correct parameters
        when optional parameters are explicitly specified
        """
        with mock.patch("lms.lib.comment_client.user.get_user_social_stats") as patched_stats:
            patched_stats.return_value = expected_result
            result = User.all_social_stats(course_key, end_date, thread_type)
            self.assertEqual(result, expected_result)
            patched_stats.assert_called_once_with('*', course_key, end_date=end_date, thread_type=thread_type)

    def test_all_social_stats_defaults(self):
        """
        Tests that all_social_stats classmethod invokes get_user_social_stats with correct parameters
        when optional parameters are omitted
        """
        with mock.patch("lms.lib.comment_client.user.get_user_social_stats") as patched_stats:
            patched_stats.return_value = {}
            course_key = CourseLocator("edX", "demoX", "now")
            User.all_social_stats(course_key)
            patched_stats.assert_called_once_with('*', course_key, end_date=None, thread_type=None)


@ddt.ddt
class UtilityTests(TestCase):
    """ Tests for utility functions found in user module """
    def test_get_user_social_stats_given_none_course_id_raises(self):
        with self.assertRaises(CommentClientRequestError):
            get_user_social_stats('irrelevant', None)

    @ddt.unpack
    @ddt.data(
        (1, CourseLocator("edX", "DemoX", "now"), None, None, "api/v1/users/1/social_stats", {}, {}),
        (
            2, CourseLocator("edX", "DemoX", "now"), datetime(2015, 01, 01), None,
            "api/v1/users/2/social_stats", {'end_date': "2015-01-01T00:00:00"}, {'2': {'num_threads': 2}}
        ),
        (
            17, CourseLocator("otherX", "CourseX", "later"), datetime(2016, 07, 15), 'discussion',
            "api/v1/users/44/social_stats", {'end_date': "2016-07-15T00:00:00", 'thread_type': 'discussion'},
            {'2': {'num_threads': 42, 'num_comments': 7}}
        ),
        (
            42, CourseLocator("otherX", "CourseX", "later"), datetime(2011, 01, 9, 17, 24, 22), 'question',
            "some/unrelated/url", {'end_date': "2011-01-09T17:24:22", 'thread_type': 'question'},
            {'28': {'num_threads': 15, 'num_comments': 96}}
        ),
    )
    def test_get_user_social_stats(self, user_id, course_id, end_date, thread_type,
                                   expected_url, expected_data, expected_result):
        """ Tests get_user_social_stats utility function """
        expected_data['course_id'] = course_id
        with mock.patch("lms.lib.comment_client.user._url_for_user_social_stats") as patched_url_for_social_stats, \
                mock.patch("lms.lib.comment_client.user.perform_request") as patched_perform_request:
            patched_perform_request.return_value = expected_result
            patched_url_for_social_stats.return_value = expected_url
            result = get_user_social_stats(user_id, course_id, end_date=end_date, thread_type=thread_type)
            patched_url_for_social_stats.assert_called_with(user_id)
            patched_perform_request.assert_called_with('get', expected_url, expected_data)
            self.assertEqual(result, expected_result)
