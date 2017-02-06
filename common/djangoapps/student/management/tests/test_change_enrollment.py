""" Test the change_enrollment command line script."""

import ddt
from mock import patch

from django.core.management import call_command
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase

from student.tests.factories import UserFactory, CourseModeFactory
from student.models import CourseEnrollment


@ddt.ddt
class ChangeEnrollmentTests(SharedModuleStoreTestCase):
    """ Test the enrollment change functionality of the change_enrollment script."""
    def setUp(self):
        super(ChangeEnrollmentTests, self).setUp()
        self.course = CourseFactory.create()
        self.audit_mode = CourseModeFactory.create(
            course_id=self.course.id,
            mode_slug='audit',
            mode_display_name='Audit',
        )
        self.honor_mode = CourseModeFactory.create(
            course_id=self.course.id,
            mode_slug='honor',
            mode_display_name='Honor',
        )

        self.user_info = [
            ('amy', 'amy@pond.com', 'password'),
            ('rory', 'rory@theroman.com', 'password'),
            ('river', 'river@song.com', 'password')
        ]
        self.enrollments = []
        self.users = []
        for username, email, password in self.user_info:
            user = UserFactory.create(username=username, email=email, password=password)
            self.users.append(user)
            self.enrollments.append(CourseEnrollment.enroll(user, self.course.id, mode='audit'))

    @patch('student.management.commands.change_enrollment.logger')
    @ddt.data(
        ('email', False, 3),
        ('username', False, 3),
        ('email', True, 0),
        ('username', True, 0),
    )
    @ddt.unpack
    def test_convert_users(self, method, noop, expected_conversions, mock_logger):
        """ The command should update the user's enrollment. """
        user_str = ','.join([getattr(user, method) for user in self.users])
        user_ids = [u.id for u in self.users]
        command_args = {
            'course_id': unicode(self.course.id),
            'to_mode': 'honor',
            'from_mode': 'audit',
            'noop': noop,
            method: user_str,
        }

        # Verify users are not in honor mode yet
        self.assertEqual(
            len(CourseEnrollment.objects.filter(mode='honor', user_id__in=user_ids)),
            0
        )

        call_command(
            'change_enrollment',
            **command_args
        )

        # Verify correct number of users are now in honor mode
        self.assertEqual(
            len(CourseEnrollment.objects.filter(mode='honor', user_id__in=user_ids)),
            expected_conversions
        )

        mock_logger.info.assert_called_with(
            'Successfully updated %i out of %i users',
            len(self.users),
            len(self.users)
        )

    @patch('student.management.commands.change_enrollment.logger')
    @ddt.data(
        ('email', 'dtennant@thedoctor.com', 3),
        ('username', 'dtennant', 3),
    )
    @ddt.unpack
    def test_user_not_found(self, method, fake_user, expected_success, mock_logger):
        all_users = [getattr(user, method) for user in self.users]
        all_users.append(fake_user)
        user_str = ','.join(all_users)
        real_user_ids = [u.id for u in self.users]
        command_args = {
            'course_id': unicode(self.course.id),
            'to_mode': 'honor',
            'from_mode': 'audit',
            method: user_str,
        }

        # Verify users are not in honor mode yet
        self.assertEqual(
            len(CourseEnrollment.objects.filter(mode='honor', user_id__in=real_user_ids)),
            0
        )

        call_command(
            'change_enrollment',
            **command_args
        )

        # Verify correct number of users are now in honor mode
        self.assertEqual(
            len(CourseEnrollment.objects.filter(mode='honor', user_id__in=real_user_ids)),
            expected_success
        )

        mock_logger.info.assert_called_with(
            'user: [%s] reason: [%s] %s', fake_user, 'DoesNotExist', 'User matching query does not exist.'
        )
