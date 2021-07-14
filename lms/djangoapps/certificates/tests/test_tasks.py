"""
Tests for course certificate tasks.
"""


from unittest import mock
from unittest.mock import patch

import ddt
from django.test import TestCase
from opaque_keys.edx.keys import CourseKey

from common.djangoapps.course_modes.models import CourseMode
from common.djangoapps.student.tests.factories import UserFactory
from lms.djangoapps.certificates.data import CertificateStatuses
from lms.djangoapps.certificates.tasks import generate_certificate


@ddt.ddt
class GenerateUserCertificateTest(TestCase):
    """
    Tests for course certificate tasks
    """
    def setUp(self):
        super().setUp()

        self.user = UserFactory()

    @ddt.data('student', 'course_key')
    def test_missing_args(self, missing_arg):
        kwargs = {'student': 'a', 'course_key': 'b', 'otherarg': 'c'}
        del kwargs[missing_arg]

        with patch('lms.djangoapps.certificates.tasks.User.objects.get'):
            with self.assertRaisesRegex(KeyError, missing_arg):
                generate_certificate.apply_async(kwargs=kwargs).get()

    def test_generation(self):
        """
        Verify the task handles certificate generation
        """
        course_key = 'course-v1:edX+DemoX+Demo_Course'

        with mock.patch(
            'lms.djangoapps.certificates.tasks.generate_course_certificate',
            return_value=None
        ) as mock_generate_cert:
            kwargs = {
                'student': self.user.id,
                'course_key': course_key
            }

            generate_certificate.apply_async(kwargs=kwargs)
            mock_generate_cert.assert_called_with(
                user=self.user,
                course_key=CourseKey.from_string(course_key),
                status=CertificateStatuses.downloadable,
                enrollment_mode=None,
                course_grade=None,
                generation_mode='batch'
            )

    def test_generation_custom(self):
        """
        Verify the task handles certificate generation custom params
        """
        course_key = 'course-v1:edX+DemoX+Demo_Course'
        gen_mode = 'self'
        status = CertificateStatuses.notpassing
        enrollment_mode = CourseMode.AUDIT
        course_grade = '0.89'

        with mock.patch(
            'lms.djangoapps.certificates.tasks.generate_course_certificate',
            return_value=None
        ) as mock_generate_cert:
            kwargs = {
                'status': status,
                'student': self.user.id,
                'course_key': course_key,
                'course_grade': course_grade,
                'enrollment_mode': enrollment_mode,
                'generation_mode': gen_mode,
                'what_about': 'dinosaurs'
            }

            generate_certificate.apply_async(kwargs=kwargs)
            mock_generate_cert.assert_called_with(
                user=self.user,
                course_key=CourseKey.from_string(course_key),
                status=status,
                enrollment_mode=enrollment_mode,
                course_grade=course_grade,
                generation_mode=gen_mode
            )
