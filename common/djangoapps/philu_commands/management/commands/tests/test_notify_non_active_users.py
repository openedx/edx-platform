"""
Tests for 'notify_non_active_users' command
"""
from datetime import datetime, timedelta

import mock
from django.conf import settings
from django.core.management import call_command
from django.db.models import signals
from factory.django import mute_signals
from pytz import utc

from common.lib.mandrill_client.client import MandrillClient
from courseware.tests.factories import StudentModuleFactory
from student.tests.factories import CourseEnrollmentFactory, UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


class TestNotifyNonActiveUsers(ModuleStoreTestCase):
    """
    Tests for 'notify_non_active_users' command
    """
    @mute_signals(signals.pre_save, signals.post_save)
    def setUp(self):
        """
        This function is responsible for creating users and course for every test enrolling users in created course.
        :return:
        """
        super(TestNotifyNonActiveUsers, self).setUp()
        self.course = CourseFactory.create(display_name='test course 1', run='Testing_course_1')

        self.user_with_course_access = self._create_user_and_enroll_in_provided_course(self.course.id)
        self.user_without_course_access = self._create_user_and_enroll_in_provided_course(self.course.id)

        StudentModuleFactory.create(student=self.user_with_course_access, course_id=self.course.id)

    @mock.patch('philu_commands.management.commands.notify_non_active_users.get_visible_courses')
    @mock.patch('philu_commands.management.commands.notify_non_active_users.get_course_open_date')
    @mock.patch('philu_commands.management.commands.notify_non_active_users.get_course_first_chapter_link')
    @mock.patch('philu_commands.management.commands.notify_non_active_users.MandrillClient.send_mail')
    @mock.patch('philu_commands.management.commands.notify_non_active_users.log.info')
    def test_notify_non_active_users_with_one_user_to_notify(
        self,
        mock_log_success_message,
        mock_send_mail,
        mock_get_course_first_chapter_link,
        mock_get_course_open_date,
        mock_get_visible_courses
    ):
        """
        Test 'notify_non_active_users' command with only one user to notify.
        """

        _, _, course_first_chapter_link = self._initialize_mock_parameters(
            mock_get_course_open_date, mock_get_visible_courses, mock_get_course_first_chapter_link)
        call_command('notify_non_active_users')

        expected_context = {
            'first_name': self.user_without_course_access.first_name,
            'course_name': self.course.display_name,
            'course_url': course_first_chapter_link
        }

        mock_send_mail.assert_called_once_with(MandrillClient.COURSE_ACTIVATION_REMINDER_TEMPLATE,
                                               self.user_without_course_access.email, expected_context)
        mock_log_success_message.assert_called_with("Emailing to %s Task Completed",
                                                    self.user_without_course_access.email)

    @mock.patch('philu_commands.management.commands.notify_non_active_users.get_visible_courses')
    @mock.patch('philu_commands.management.commands.notify_non_active_users.get_course_open_date')
    @mock.patch('philu_commands.management.commands.notify_non_active_users.get_course_first_chapter_link')
    @mock.patch('philu_commands.management.commands.notify_non_active_users.MandrillClient.send_mail')
    def test_notify_non_active_users_with_multiple_users_to_notify(
        self,
        mock_send_mail,
        mock_get_course_first_chapter_link,
        mock_get_course_open_date,
        mock_get_visible_courses
    ):
        """
        Test 'notify_non_active_users' command with 2 users to notify.
        """
        self._initialize_mock_parameters(
            mock_get_course_open_date, mock_get_visible_courses, mock_get_course_first_chapter_link)

        self._create_user_and_enroll_in_provided_course(self.course.id)

        call_command('notify_non_active_users')
        self.assertEqual(mock_send_mail.call_count, 2)

    @mute_signals(signals.pre_save, signals.post_save)
    @mock.patch('philu_commands.management.commands.notify_non_active_users.get_visible_courses')
    @mock.patch('philu_commands.management.commands.notify_non_active_users.get_course_open_date')
    @mock.patch('philu_commands.management.commands.notify_non_active_users.get_course_first_chapter_link')
    @mock.patch('philu_commands.management.commands.notify_non_active_users.MandrillClient.send_mail')
    def test_notify_non_active_users_with_no_users_to_notify(
        self,
        mock_send_mail,
        mock_get_course_first_chapter_link,
        mock_get_course_open_date,
        mock_get_visible_courses
    ):
        """
        Test 'notify_non_active_users' command with no users to notify.
        """
        self._initialize_mock_parameters(
            mock_get_course_open_date, mock_get_visible_courses, mock_get_course_first_chapter_link)

        second_user_without_course_access = self._create_user_and_enroll_in_provided_course(self.course.id)

        StudentModuleFactory.create(student=self.user_without_course_access, course_id=self.course.id)
        StudentModuleFactory.create(student=second_user_without_course_access, course_id=self.course.id)

        call_command('notify_non_active_users')
        assert not mock_send_mail.called

    @mock.patch('philu_commands.management.commands.notify_non_active_users.get_visible_courses')
    @mock.patch('philu_commands.management.commands.notify_non_active_users.get_course_open_date')
    @mock.patch('philu_commands.management.commands.notify_non_active_users.get_course_first_chapter_link')
    @mock.patch('philu_commands.management.commands.notify_non_active_users.MandrillClient.send_mail')
    def test_notify_non_active_users_with_invalid_dates(
        self,
        mock_send_mail,
        mock_get_course_first_chapter_link,
        mock_get_course_open_date,
        mock_get_visible_courses
    ):
        """
        Test 'notify_non_active_users' command by running command prior to and later than 7 days after
        course_open_date.
        """
        mock_get_visible_courses.return_value = [self.course]

        three_days_before_today = datetime.now(utc) - timedelta(days=3)
        mock_get_course_open_date.return_value = three_days_before_today

        call_command('notify_non_active_users')
        assert not mock_get_course_first_chapter_link.called
        assert not mock_send_mail.called

        ten_days_before_today = datetime.now(utc) - timedelta(days=10)
        mock_get_course_open_date.return_value = ten_days_before_today

        call_command('notify_non_active_users')
        assert not mock_get_course_first_chapter_link.called
        assert not mock_send_mail.called

    def _initialize_mock_parameters(self, course_open_date, all_courses, course_first_chapter_link):
        """
        This function initializes mock objects.
        Args:
            course_open_date (mock): Mock object for course_open_date
            all_courses (mock): Mock object for all_courses
            course_first_chapter_link (mock): Mock object for course_first_chapter_link
        Returns:
            tuple: (course_open_date, all_courses, course_first_chapter_link)
        """
        start_date = datetime.now(utc) - timedelta(days=7)

        course_open_date.return_value = start_date
        all_courses.return_value = [self.course]

        course_first_chapter_link.return_value = '{base_url}/courses/{course_id}/courseware/chapter_id/sequence_id/'\
            .format(
                base_url=settings.LMS_ROOT_URL,
                course_id=str(self.course.id)
            )
        return course_open_date, all_courses, course_first_chapter_link.return_value

    def _create_user_and_enroll_in_provided_course(self, course_id):
        """
        This function creates user and enrolls user in provided course.
        Args:
            course_id (CourseKey): ID of course
        Returns:
            User: Newly created user
        """
        user = UserFactory()
        CourseEnrollmentFactory.create(user=user, course_id=course_id, is_active=True)
        return user
