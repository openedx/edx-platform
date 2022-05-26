"""
Tests for the send_program_course_nudge_email management command.
"""
from datetime import timedelta
from unittest.mock import patch

import ddt
from django.core.management import call_command
from django.test import TestCase
from django.test.utils import override_settings
from django.utils import timezone
from testfixtures import LogCapture

from common.djangoapps.student.tests.factories import UserFactory
from lms.djangoapps.grades.models import PersistentCourseGrade
from openedx.core.djangoapps.catalog.tests.factories import CourseFactory, CourseRunFactory, ProgramFactory
from openedx.features.enterprise_support.tests.factories import EnterpriseCustomerUserFactory

LOG_PATH = 'lms.djangoapps.program_enrollments.management.commands.send_program_course_nudge_email'


@ddt.ddt
class TestSendProgramCourseNudgeEmailCommand(TestCase):
    """
    Test send_program_course_nudge_email command.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.command = 'send_program_course_nudge_email'

    def setUp(self):
        super().setUp()
        self.user_1 = UserFactory()
        self.user_2 = UserFactory()

        self.enterprise_customer_user = EnterpriseCustomerUserFactory.create(
            user_id=self.user_1.id, enterprise_customer__enable_learner_portal=True
        )

        self.enrolled_course_run = CourseRunFactory()
        self.course_run_1 = CourseRunFactory()
        self.course_run_2 = CourseRunFactory()
        self.enrolled_course = CourseFactory(course_runs=[self.enrolled_course_run])
        self.unenrolled_course_1 = CourseFactory(course_runs=[self.course_run_1])
        self.unenrolled_course_2 = CourseFactory(course_runs=[self.course_run_2])

        self.enrolled_program_1 = ProgramFactory(
            courses=[self.enrolled_course, self.unenrolled_course_1],
            type='MicroBachelors'
        )
        self.enrolled_program_2 = ProgramFactory(
            courses=[self.enrolled_course, self.unenrolled_course_2],
            type='MicroMasters'
        )
        self.enrolled_program_3 = ProgramFactory(
            courses=[self.enrolled_course],
            type='MicroMasters'
        )
        self.unenrolled_program = ProgramFactory()
        self.create_grade(user_id=self.user_1.id, course_id=self.enrolled_course_run['key'])
        self.create_grade(user_id=self.user_2.id, course_id=self.enrolled_course_run['key'])

        self.all_programs = [self.enrolled_program_1, self.enrolled_program_2, self.unenrolled_program]

    def create_grade(self, user_id, course_id):
        """
        Create PersistentCourseGrade records for given user and course
        """
        params = {
            "user_id": user_id,
            "course_id": course_id,
            "course_version": "JoeMcEwing",
            "percent_grade": 77.7,
            "letter_grade": "Great job",
            "passed_timestamp": timezone.now() - timedelta(days=1),
        }
        PersistentCourseGrade.objects.create(**params)

    @ddt.data(
        False, True
    )
    @patch('common.djangoapps.student.models.segment.track')
    @patch('lms.djangoapps.program_enrollments.management.commands.send_program_course_nudge_email.get_programs')
    @override_settings(FEATURES=dict(ENABLE_ENTERPRISE_INTEGRATION=True))
    def test_email_send(self, add_no_commit, get_programs_mock, mock_track):
        """
        Test Segment fired as expected.
        """
        get_programs_mock.return_value = [self.enrolled_program_1, self.enrolled_program_2]
        with LogCapture() as logger:
            if add_no_commit:
                call_command(self.command, '--no-commit')
            else:
                call_command(self.command)
            logger.check_present(
                (
                    LOG_PATH,
                    'INFO',
                    f"[Program Course Nudge Email] 2 Emails sent. Records: ["
                    f"'User: {self.user_1.username}, Completed Course: {self.enrolled_course_run['key']},"
                    f" Suggested Course: {self.course_run_2['key']}', "
                    f"'User: {self.user_2.username}, Completed Course: {self.enrolled_course_run['key']},"
                    f" Suggested Course: {self.course_run_2['key']}']"
                )
            )
            if add_no_commit:
                assert mock_track.call_count == 0
            else:
                assert mock_track.call_count == 2

    @ddt.data(
        False, True
    )
    @patch('common.djangoapps.student.models.segment.track')
    @patch('lms.djangoapps.program_enrollments.management.commands.send_program_course_nudge_email.get_programs')
    @override_settings(FEATURES=dict(ENABLE_ENTERPRISE_INTEGRATION=True))
    def test_email_no_course_recommendation(self, add_no_commit, get_programs_mock, mock_track):
        """
        Test Segment fired as expected.
        """
        get_programs_mock.return_value = [self.enrolled_program_3]
        with LogCapture() as logger:
            if add_no_commit:
                call_command(self.command, '--no-commit')
            else:
                call_command(self.command)
            logger.check_present(
                (
                    LOG_PATH,
                    'INFO',
                    '[Program Course Nudge Email] 0 Emails sent. Records: []'
                )
            )
            assert mock_track.call_count == 0
