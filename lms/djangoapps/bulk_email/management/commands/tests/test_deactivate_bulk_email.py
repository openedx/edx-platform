from mock import patch, MagicMock, ANY

from django.core.management.base import CommandError
from django.test import TestCase
from django.test.utils import override_settings

from bulk_email.management.commands import deactivate_bulk_email
from bulk_email.management.commands.tests.factories import OptoutFactory
from student.tests.factories import CourseEnrollmentFactory, UserFactory
from xmodule.modulestore.tests.factories import CourseFactory
from courseware.tests.modulestore_config import TEST_DATA_MIXED_MODULESTORE


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class BulkEmailCommandTestCase(TestCase):

    def setUp(self):

        self.kwargs = {"course_id": None, "reactivate": False}
        ###dummy course
        self.course = CourseFactory.create()

        self.course_kwargs = {"course_id": self.course.id.to_deprecated_string(), "reactivate": False}

        ###testuser1 (enrolled one course and no optout)
        self.user = UserFactory.create(username="testuser1", email="testuser1@example.com")
        CourseEnrollmentFactory.create(user=self.user, course_id=self.course.id)
        self.args = [self.user.email]

        ###testuser1 reactivate(enrolled one course and no optout)
        self.reactivate_kwargs = {"course_id": None, "reactivate": True}

        ###testuser2 (enrolled no course and no optout)
        self.nocourse_user = UserFactory.create(username="testuser2", email="testuser2@example.com")
        self.nocourse_args = [self.nocourse_user.email]

        ###testuser3 (enrolled one course and force optout)
        self.forcedisabled_user = UserFactory.create(username="testuser3", email="testuser3@example.com")
        CourseEnrollmentFactory.create(user=self.forcedisabled_user, course_id=self.course.id)
        OptoutFactory.create(user=self.forcedisabled_user, course_id=self.course.id, force_disabled=True)
        self.forcedisabled_args = [self.forcedisabled_user.email]

        ###testuser4 (enrolled one course and with optout by user)
        self.userdisabled_user = UserFactory.create(username="testuser4", email="testuser4@example.com")
        CourseEnrollmentFactory.create(user=self.userdisabled_user, course_id=self.course.id)
        OptoutFactory.create(user=self.userdisabled_user, course_id=self.course.id, force_disabled=False)
        self.userdisabled_args = [self.userdisabled_user.email]

        ### if numbers of args are two.
        self.toomanyargs_args = ["aaa", "bbb"]

        ### not existing user
        self.nouser_args = ["hogehoge"]

    def tearDown(self):
        pass

    @patch('bulk_email.management.commands.deactivate_bulk_email.Optout.objects.create')
    def test_handle_deactivate(self, optout_mock):
        with patch('bulk_email.management.commands.deactivate_bulk_email.get_user_by_username_or_email', return_value=self.user) as user_mock:
            deactivate_bulk_email.Command().handle(*self.args, **self.kwargs)
            user_mock.assert_called_once_with("testuser1@example.com")
            optout_mock.assert_called_once_with(course_id=self.course.id, force_disabled=True, user=self.user)

    @patch('bulk_email.management.commands.deactivate_bulk_email.Optout.objects.filter')
    def test_handle_reactivate(self, optout_mock):
        with patch('bulk_email.management.commands.deactivate_bulk_email.get_user_by_username_or_email', return_value=self.user) as user_mock:
            deactivate_bulk_email.Command().handle(*self.args, **self.reactivate_kwargs)
            user_mock.assert_called_once_with("testuser1@example.com")
            optout_mock.assert_called_once_with(course_id=self.course.id, user=self.user)

    def test_handle_course_deactivate(self):
        with patch('bulk_email.management.commands.deactivate_bulk_email.get_user_by_username_or_email', return_value=self.user) as user_mock:
            deactivate_bulk_email.Command().handle(*self.args, **self.course_kwargs)
            user_mock.assert_called_once_with("testuser1@example.com")

    def test_handle_nocourse(self):
        with patch('bulk_email.management.commands.deactivate_bulk_email.get_user_by_username_or_email', return_value=self.nocourse_user) as nocourse_user_mock:
            deactivate_bulk_email.Command().handle(*self.nocourse_args, **self.kwargs)
            nocourse_user_mock.assert_called_once_with("testuser2@example.com")

    def test_handle_forcedisabled(self):
        with patch('bulk_email.management.commands.deactivate_bulk_email.get_user_by_username_or_email', return_value=self.forcedisabled_user) as forcedisabled_user_mock:
            deactivate_bulk_email.Command().handle(*self.forcedisabled_args, **self.kwargs)
            forcedisabled_user_mock.assert_called_once_with("testuser3@example.com")

    def test_handle_userdisabled(self):
        with patch('bulk_email.management.commands.deactivate_bulk_email.get_user_by_username_or_email', return_value=self.userdisabled_user) as userdisabled_user_mock:
            deactivate_bulk_email.Command().handle(*self.userdisabled_args, **self.kwargs)
            userdisabled_user_mock.assert_called_once_with("testuser4@example.com")

    def test_handle_toomanyargs(self):
        with self.assertRaises(CommandError):
            deactivate_bulk_email.Command().handle(*self.toomanyargs_args, **self.kwargs)

    def test_handle_nouser(self):
        with self.assertRaises(CommandError):
            deactivate_bulk_email.Command().handle(*self.nouser_args, **self.kwargs)
