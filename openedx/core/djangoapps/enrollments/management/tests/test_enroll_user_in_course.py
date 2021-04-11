""" Test the change_enrollment command line script."""


import unittest
from uuid import uuid4
import ddt

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError

from openedx.core.djangoapps.enrollments.api import get_enrollment
from common.djangoapps.student.tests.factories import UserFactory

from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
import six
from six.moves import range


@ddt.ddt
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class EnrollManagementCommandTest(SharedModuleStoreTestCase):
    """
    Test the enroll_user_in_course management command
    """

    @classmethod
    def setUpClass(cls):
        super(EnrollManagementCommandTest, cls).setUpClass()
        cls.course = CourseFactory.create(org='fooX', number='007')

    def setUp(self):
        super(EnrollManagementCommandTest, self).setUp()
        self.course_id = six.text_type(self.course.id)
        self.username = 'ralph' + uuid4().hex
        self.user_email = self.username + '@example.com'

        UserFactory(username=self.username, email=self.user_email)

    def test_enroll_user(self):

        command_args = [
            '--course', self.course_id,
            '--email', self.user_email,
        ]

        call_command(
            'enroll_user_in_course',
            *command_args
        )

        user_enroll = get_enrollment(self.username, self.course_id)
        self.assertTrue(user_enroll['is_active'])

    def test_enroll_user_twice(self):
        """
        Ensures the command is idempotent.
        """

        command_args = [
            '--course', self.course_id,
            '--email', self.user_email,
        ]

        for _ in range(2):
            call_command(
                'enroll_user_in_course',
                *command_args
            )

        # Second run does not impact the first run (i.e., the
        # user is still enrolled, no exception was raised, etc)
        user_enroll = get_enrollment(self.username, self.course_id)
        self.assertTrue(user_enroll['is_active'])

    @ddt.data(['--email', 'foo'], ['--course', 'bar'], ['--bad-param', 'baz'])
    def test_not_enough_args(self, arg):
        """
        When the command is missing certain arguments, it should
        raise an exception
        """

        command_args = arg

        with self.assertRaises(CommandError):
            call_command(
                'enroll_user_in_course',
                *command_args
            )
