"""
Tests the ``notify_credentials`` management command.
"""
from __future__ import absolute_import, unicode_literals
from __future__ import print_function

from datetime import datetime
import mock

from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection, reset_queries
from django.test import TestCase, override_settings
from freezegun import freeze_time

from lms.djangoapps.certificates.tests.factories import GeneratedCertificateFactory
from lms.djangoapps.grades.models import PersistentCourseGrade
from openedx.core.djangoapps.credentials.models import NotifyCredentialsConfig
from openedx.core.djangoapps.site_configuration.tests.factories import SiteConfigurationFactory
from openedx.core.djangolib.testing.utils import skip_unless_lms
from student.tests.factories import UserFactory

from ..notify_credentials import Command

COMMAND_MODULE = 'openedx.core.djangoapps.credentials.management.commands.notify_credentials'


@skip_unless_lms
class TestNotifyCredentials(TestCase):
    """
    Tests the ``notify_credentials`` management command.
    """
    def setUp(self):
        super(TestNotifyCredentials, self).setUp()
        self.user = UserFactory.create()

        with freeze_time(datetime(2017, 1, 1)):
            self.cert1 = GeneratedCertificateFactory(user=self.user, course_id='course-v1:edX+Test+1')
        with freeze_time(datetime(2017, 2, 1)):
            self.cert2 = GeneratedCertificateFactory(user=self.user, course_id='course-v1:edX+Test+2')
        with freeze_time(datetime(2017, 3, 1)):
            self.cert3 = GeneratedCertificateFactory(user=self.user, course_id='course-v1:testX+Test+3')
        print(('self.cert1.modified_date', self.cert1.modified_date))

        # No factory for these
        with freeze_time(datetime(2017, 1, 1)):
            self.grade1 = PersistentCourseGrade.objects.create(user_id=self.user.id, course_id='course-v1:edX+Test+1',
                                                               percent_grade=1)
        with freeze_time(datetime(2017, 2, 1)):
            self.grade2 = PersistentCourseGrade.objects.create(user_id=self.user.id, course_id='course-v1:edX+Test+2',
                                                               percent_grade=1)
        with freeze_time(datetime(2017, 3, 1)):
            self.grade3 = PersistentCourseGrade.objects.create(user_id=self.user.id, course_id='course-v1:testX+Test+3',
                                                               percent_grade=1)
        print(('self.grade1.modified', self.grade1.modified))

    @mock.patch(COMMAND_MODULE + '.Command.send_notifications')
    def test_course_args(self, mock_send):
        call_command(Command(), '--course', 'course-v1:edX+Test+1', 'course-v1:edX+Test+2')
        self.assertTrue(mock_send.called)
        self.assertEqual(list(mock_send.call_args[0][0]), [self.cert1, self.cert2])
        self.assertEqual(list(mock_send.call_args[0][1]), [self.grade1, self.grade2])

    @mock.patch(COMMAND_MODULE + '.Command.send_notifications')
    def test_date_args(self, mock_send):
        call_command(Command(), '--start-date', '2017-01-31')
        self.assertTrue(mock_send.called)
        self.assertListEqual(list(mock_send.call_args[0][0]), [self.cert2, self.cert3])
        self.assertListEqual(list(mock_send.call_args[0][1]), [self.grade2, self.grade3])
        mock_send.reset_mock()

        call_command(Command(), '--start-date', '2017-02-01', '--end-date', '2017-02-02')
        self.assertTrue(mock_send.called)
        self.assertListEqual(list(mock_send.call_args[0][0]), [self.cert2])
        self.assertListEqual(list(mock_send.call_args[0][1]), [self.grade2])
        mock_send.reset_mock()

        call_command(Command(), '--end-date', '2017-02-02')
        self.assertTrue(mock_send.called)
        self.assertListEqual(list(mock_send.call_args[0][0]), [self.cert1, self.cert2])
        self.assertListEqual(list(mock_send.call_args[0][1]), [self.grade1, self.grade2])

    @mock.patch(COMMAND_MODULE + '.Command.send_notifications')
    def test_no_args(self, mock_send):
        with self.assertRaisesRegex(CommandError, 'You must specify a filter.*'):
            call_command(Command())
        self.assertFalse(mock_send.called)

    @mock.patch(COMMAND_MODULE + '.Command.send_notifications')
    def test_dry_run(self, mock_send):
        call_command(Command(), '--dry-run', '--start-date', '2017-02-01')
        self.assertFalse(mock_send.called)

    @mock.patch(COMMAND_MODULE + '.handle_cert_change')
    @mock.patch(COMMAND_MODULE + '.send_grade_if_interesting')
    @mock.patch(COMMAND_MODULE + '.handle_course_cert_changed')
    def test_hand_off(self, mock_grade_cert_change, mock_grade_interesting, mock_program_changed):
        call_command(Command(), '--start-date', '2017-02-01')
        self.assertEqual(mock_grade_cert_change.call_count, 2)
        self.assertEqual(mock_grade_interesting.call_count, 2)
        self.assertEqual(mock_program_changed.call_count, 2)

    @mock.patch(COMMAND_MODULE + '.time')
    def test_delay(self, mock_time):
        call_command(Command(), '--start-date', '2017-01-01', '--page-size=2')
        self.assertEqual(mock_time.sleep.call_count, 0)
        mock_time.sleep.reset_mock()

        call_command(Command(), '--start-date', '2017-01-01', '--page-size=2', '--delay', '0.2')
        self.assertEqual(mock_time.sleep.call_count, 2)  # Between each page, twice (2 pages, for certs and grades)
        self.assertEqual(mock_time.sleep.call_args[0][0], 0.2)

    @override_settings(DEBUG=True)
    def test_page_size(self):
        reset_queries()
        call_command(Command(), '--start-date', '2017-01-01')
        baseline = len(connection.queries)

        reset_queries()
        call_command(Command(), '--start-date', '2017-01-01', '--page-size=1')
        self.assertEqual(len(connection.queries), baseline + 4)  # two extra page queries each for certs & grades

        reset_queries()
        call_command(Command(), '--start-date', '2017-01-01', '--page-size=2')
        self.assertEqual(len(connection.queries), baseline + 2)  # one extra page query each for certs & grades

    @mock.patch(COMMAND_MODULE + '.send_grade_if_interesting')
    @mock.patch(COMMAND_MODULE + '.handle_cert_change')
    def test_site(self, mock_grade_interesting, mock_cert_change):
        site_config = SiteConfigurationFactory.create(
            values={'course_org_filter': ['testX']},
        )

        call_command(Command(), '--site', site_config.site.domain, '--start-date', '2017-01-01')
        self.assertEqual(mock_grade_interesting.call_count, 1)
        self.assertEqual(mock_cert_change.call_count, 1)

    @mock.patch(COMMAND_MODULE + '.Command.send_notifications')
    def test_args_from_database(self, mock_send):
        # Nothing in the database, should default to disabled
        with self.assertRaisesRegex(CommandError, 'NotifyCredentialsConfig is disabled.*'):
            call_command(Command(), '--start-date', '2017-01-01', '--args-from-database')

        # Add a config
        config = NotifyCredentialsConfig.current()
        config.arguments = '--start-date 2017-03-01'
        config.enabled = True
        config.save()

        # Not told to use config, should ignore it
        call_command(Command(), '--start-date', '2017-01-01')
        self.assertEqual(len(mock_send.call_args[0][0]), 3)

        # Told to use it, and enabled. Should use config in preference of command line
        call_command(Command(), '--start-date', '2017-01-01', '--args-from-database')
        self.assertEqual(len(mock_send.call_args[0][0]), 1)

        config.enabled = False
        config.save()

        # Explicitly disabled
        with self.assertRaisesRegex(CommandError, 'NotifyCredentialsConfig is disabled.*'):
            call_command(Command(), '--start-date', '2017-01-01', '--args-from-database')
