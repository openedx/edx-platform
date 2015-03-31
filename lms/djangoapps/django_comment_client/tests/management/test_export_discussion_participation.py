""" Tests for export discussion participation statistics command"""
import ddt
from StringIO import StringIO
import mock
from django.test import TestCase
from django.core.management.base import CommandError
from django.contrib.auth.models import User

from opaque_keys.edx.locator import CourseLocator
from opaque_keys import InvalidKeyError

import django_comment_client.utils as utils
from django_comment_client.management.commands.export_discussion_participation import (
    Command as ExportDiscussionCommand, Extractor, Exporter, DiscussionExportFields
)
from datetime import datetime

# pylint: disable=invalid-name
_target_module = "django_comment_client.management.commands.export_discussion_participation"

_std_parameters_list = (
    (CourseLocator(org="edX", course="demoX", run="now"), None, None),
    (CourseLocator(org="otherX", course="courseX", run="later"), datetime(2015, 2, 12), None),
    (CourseLocator(org="NotAX", course="NotADemo", run="anyyear"), None, 'discussion'),
    (CourseLocator(org="YeaAX", course="YesADemo", run="anyday"), None, 'question'),
    (CourseLocator(org="WhatX", course="WhatADemo", run="last_year"), datetime(2014, 3, 17), 'question')
)
# pylint: enable=invalid-name


@ddt.ddt
@mock.patch(_target_module + ".get_course")
class CommandTest(TestCase):
    """
    Tests that command correctly parses arguments, creates helper class instances and invokes correct
    methods on them
    """
    def setUp(self):
        """ Test setup """
        super(CommandTest, self).setUp()
        self.command = ExportDiscussionCommand()
        self.command.stdout = mock.Mock()
        self.command.stderr = mock.Mock()

    def set_up_default_mocks(self, patched_get_courses):
        """ Sets up default mocks passed via class decorator """
        patched_get_courses.return_value = CourseLocator("edX", "demoX", "now")

    # pylint:disable=unused-argument
    def test_handle_given_no_arguments_raises_command_error(self, patched_get_courses):
        """ Tests that raises error if invoked with no arguments """
        with self.assertRaises(CommandError):
            self.command.handle()

    # pylint:disable=unused-argument
    def test_handle_given_more_than_two_args_raises_command_error(self, patched_get_courses):
        """ Tests that raises error if invoked with too many arguments """
        with self.assertRaises(CommandError):
            self.command.handle(1, 2, 3)

    def test_handle_given_invalid_course_key_raises_invalid_key_error(self, patched_get_courses):
        """ Tests that invalid key errors are propagated """
        patched_get_courses.return_value = None
        with self.assertRaises(InvalidKeyError):
            self.command.handle("I'm invalid key")

    def test_handle_given_missing_course_raises_command_error(self, patched_get_courses):
        """ Tests that raises command error if missing course key was provided """
        patched_get_courses.return_value = None
        with self.assertRaises(CommandError):
            self.command.handle("edX/demoX/now")

    @ddt.data("edX/demoX/now", "otherX/CourseX/later")
    def test_handle_writes_to_correct_location_when_output_file_not_specified(self, course_key, patched_get_courses):
        """ Tests that when no explicit filename is given data is exported to default location """
        self.set_up_default_mocks(patched_get_courses)
        expected_filename = utils.format_filename(
            "social_stats_{course}_{date:%Y_%m_%d_%H_%M_%S}.csv".format(course=course_key, date=datetime.utcnow())
        )
        patched_open = mock.mock_open()
        with mock.patch("{}.open".format(_target_module), patched_open, create=True), \
                mock.patch(_target_module + ".Extractor.extract") as patched_extractor:
            patched_extractor.return_value = []
            self.command.handle(course_key)
            patched_open.assert_called_with(expected_filename, 'wb')

    @ddt.data("test.csv", "other_file.csv")
    def test_handle_writes_to_correct_location_when_output_file_is_specified(self, location, patched_get_courses):
        """ Tests that when explicit filename is given data is exported to chosen location """
        self.set_up_default_mocks(patched_get_courses)
        patched_open = mock.mock_open()
        with mock.patch("{}.open".format(_target_module), patched_open, create=True), \
                mock.patch(_target_module + ".Extractor.extract") as patched_extractor:
            patched_extractor.return_value = []
            self.command.handle("irrelevant/course/key", location)
            patched_open.assert_called_with(location, 'wb')

    def test_handle_creates_correct_exporter(self, patched_get_courses):
        """ Tests that creates correct exporter """
        self.set_up_default_mocks(patched_get_courses)
        patched_open = mock.mock_open()
        with mock.patch("{}.open".format(_target_module), patched_open, create=True), \
                mock.patch(_target_module + ".Extractor.extract") as patched_extractor, \
                mock.patch(_target_module + ".Exporter") as patched_exporter:
            open_retval = patched_open()
            patched_extractor.return_value = []
            self.command.handle("irrelevant/course/key", "irrelevant_location.csv")
            patched_exporter.assert_called_with(open_retval)

    @ddt.data(
        {},
        {"1": {"num_threads": 12}},
        {"1": {"num_threads": 14, "num_comments": 7}}
    )
    def test_handle_exports_correct_data(self, extracted, patched_get_courses):
        """ Tests that invokes export with correct data """
        self.set_up_default_mocks(patched_get_courses)
        patched_open = mock.mock_open()
        with mock.patch("{}.open".format(_target_module), patched_open, create=True), \
                mock.patch(_target_module + ".Extractor.extract") as patched_extractor, \
                mock.patch(_target_module + ".Exporter.export") as patched_exporter:
            patched_extractor.return_value = extracted
            self.command.handle("irrelevant/course/key", "irrelevant_location.csv")
            patched_exporter.assert_called_with(extracted)

    @ddt.unpack
    @ddt.data(*_std_parameters_list)
    def test_handle_passes_correct_parameters_to_extractor(
        self, course_key, end_date, thread_type, patched_get_courses
    ):
        """ Tests that when no explicit filename is given data is exported to default location """
        self.set_up_default_mocks(patched_get_courses)
        patched_open = mock.mock_open()
        with mock.patch("{}.open".format(_target_module), patched_open, create=True), \
                mock.patch(_target_module + ".Extractor.extract") as patched_extractor:
            patched_extractor.return_value = []
            self.command.handle(
                str(course_key),
                end_date=end_date.isoformat() if end_date else end_date,
                thread_type=thread_type
            )
            patched_extractor.assert_called_with(course_key, end_date=end_date, thread_type=thread_type)


def _make_user_mock(user_id, username="", email="", first_name="", last_name=""):
    """ Builds user data mock """
    result = mock.Mock(spec=User)
    result.id = user_id
    result.username = username
    result.email = email
    result.first_name = first_name
    result.last_name = last_name
    return result


def _make_social_stats(**kwargs):
    """ Builds discussion participation data"""
    result = {
        DiscussionExportFields.THREADS: 0,
        DiscussionExportFields.COMMENTS: 0,
        DiscussionExportFields.REPLIES: 0,
        DiscussionExportFields.UPVOTES: 0,
        DiscussionExportFields.FOLOWERS: 0,
        DiscussionExportFields.COMMENTS_GENERATED: 0,
        DiscussionExportFields.THREADS_READ: 0,
    }
    result.update(kwargs)
    return result


def _make_result(user_id, **kwargs):
    """ Builds single data item as returned by Extractor """
    result = {
        DiscussionExportFields.USER_ID: user_id,
        DiscussionExportFields.USERNAME: "",
        DiscussionExportFields.EMAIL: "",
        DiscussionExportFields.FIRST_NAME: "",
        DiscussionExportFields.LAST_NAME: "",
        DiscussionExportFields.THREADS: 0,
        DiscussionExportFields.COMMENTS: 0,
        DiscussionExportFields.REPLIES: 0,
        DiscussionExportFields.UPVOTES: 0,
        DiscussionExportFields.FOLOWERS: 0,
        DiscussionExportFields.COMMENTS_GENERATED: 0,
        DiscussionExportFields.THREADS_READ: 0,
    }
    result.update(kwargs)
    return result


@ddt.ddt
class ExtractorTest(TestCase):
    """ Tests that Extractor extracts correct data and transforms it into expected format """
    def setUp(self):
        super(ExtractorTest, self).setUp()
        self.extractor = Extractor()

    @ddt.unpack
    @ddt.data(*_std_parameters_list)
    def test_extract_invokes_correct_data_extraction_methods(self, course_key, end_date, thread_type):
        """ Tests that correct underlying extractors are called with proper arguments """
        with mock.patch(_target_module + '.CourseEnrollment.users_enrolled_in') as patched_users_enrolled_in, \
                mock.patch(_target_module + ".User.all_social_stats") as patched_all_social_stats:
            self.extractor.extract(course_key, end_date=end_date, thread_type=thread_type)
            patched_users_enrolled_in.return_value = []
            patched_users_enrolled_in.patched_all_social_stats = {}
            patched_users_enrolled_in.assert_called_with(course_key)
            patched_all_social_stats.assert_called_with(str(course_key), end_date=end_date, thread_type=thread_type)

    @ddt.unpack
    @ddt.data(
        ([], {}, []),
        (
            [_make_user_mock(1)],
            {"1": _make_social_stats(num_threads=1)},
            [_make_result(1, num_threads=1)]
        ),
        (
            [
                _make_user_mock(1, username="Q", email="q@e.com", first_name="w", last_name="e"),
                _make_user_mock(2, username="A", email="a@d.com", first_name="s", last_name="d"),
                _make_user_mock(3, username="z", email="z@c.com", first_name="x", last_name="c"),
            ],
            {
                "1": _make_social_stats(
                    num_threads=1, num_comments=3, num_replies=7,
                    num_upvotes=2, num_thread_followers=4, num_comments_generated=4
                ),
                "2": _make_social_stats(
                    num_threads=7, num_comments=15, num_replies=3,
                    num_upvotes=4, num_thread_followers=5, num_comments_generated=19
                )
            },
            [
                _make_result(
                    1, username="Q", email="q@e.com", first_name="w", last_name="e",
                    num_threads=1, num_comments=3, num_replies=7,
                    num_upvotes=2, num_thread_followers=4, num_comments_generated=4
                ),
                _make_result(
                    2, username="A", email="a@d.com", first_name="s", last_name="d",
                    num_threads=7, num_comments=15, num_replies=3,
                    num_upvotes=4, num_thread_followers=5, num_comments_generated=19
                ),
                _make_result(3, username="z", email="z@c.com", first_name="x", last_name="c")
            ]
        ),
    )
    def test_extract_correctly_merges_data(self, user_data, social_stats, expected_result):
        """ Tests that extracted data is merged correctly """
        with mock.patch(_target_module + '.CourseEnrollment.users_enrolled_in') as patched_users_enrolled_in, \
                mock.patch(_target_module + ".User.all_social_stats") as patched_all_social_stats:
            patched_users_enrolled_in.return_value = user_data
            patched_all_social_stats.return_value = social_stats

            result = self.extractor.extract(CourseLocator("completely", "irrelevant", "here"))
            self.assertEqual(sorted(result, key=lambda i: i[DiscussionExportFields.USER_ID]), expected_result)


class ExporterTest(TestCase):
    """ Tests Exporter class"""
    def test_export_export_correct_csv_to_selected_stream(self):
        """ Tests that exporter creates correct dict writer """
        stream = StringIO()
        exporter = Exporter(stream)
        exporter.export([
            _make_result(
                1, username=u"Q", email=u"q@e.com", first_name=u"w", last_name=u"e",
                num_threads=1, num_comments=3, num_replies=7,
                num_upvotes=2, num_thread_followers=4, num_comments_generated=4,
                num_threads_read=2,
            ),
            _make_result(
                2, username="A", email="a@d.com", first_name="s", last_name="d",
                num_threads=7, num_comments=15, num_replies=3,
                num_upvotes=4, num_thread_followers=5, num_comments_generated=19,
                num_threads_read=3,
            )
        ])
        lines = stream.getvalue().split("\r\n")
        self.assertEqual(len(lines), 4)
        self.assertEqual(lines[0], u",".join(exporter.row_order))
        self.assertEqual(lines[1], u"A,a@d.com,s,d,2,7,15,3,4,5,19,3")
        self.assertEqual(lines[2], u"Q,q@e.com,w,e,1,1,3,7,2,4,4,2")
        self.assertEqual(lines[3], u"")
