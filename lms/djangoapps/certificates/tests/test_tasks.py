"""
Test module for user certificate generation.
"""


import ddt
from django.test import TestCase
from mock import call, patch
from opaque_keys.edx.keys import CourseKey

from lms.djangoapps.certificates.tasks import generate_certificate
from lms.djangoapps.verify_student.models import IDVerificationAttempt
from common.djangoapps.student.tests.factories import UserFactory


@ddt.ddt
class GenerateUserCertificateTest(TestCase):

    @patch('lms.djangoapps.certificates.tasks.generate_user_certificates')
    @patch('lms.djangoapps.certificates.tasks.User.objects.get')
    def test_generate_user_certs(self, user_get_mock, generate_user_certs_mock):
        course_key = 'course-v1:edX+CS101+2017_T2'
        kwargs = {
            'student': 'student-id',
            'course_key': course_key,
            'otherarg': 'c',
            'otherotherarg': 'd'
        }
        generate_certificate.apply_async(kwargs=kwargs).get()

        expected_student = user_get_mock.return_value
        generate_user_certs_mock.assert_called_with(
            student=expected_student,
            course_key=CourseKey.from_string(course_key),
            otherarg='c',
            otherotherarg='d'
        )
        user_get_mock.assert_called_once_with(id='student-id')

    @ddt.data('student', 'course_key')
    def test_missing_args(self, missing_arg):
        kwargs = {'student': 'a', 'course_key': 'b', 'otherarg': 'c'}
        del kwargs[missing_arg]

        with patch('lms.djangoapps.certificates.tasks.User.objects.get'):
            with self.assertRaisesRegex(KeyError, missing_arg):
                generate_certificate.apply_async(kwargs=kwargs).get()

    @patch('lms.djangoapps.certificates.tasks.generate_user_certificates')
    @patch('lms.djangoapps.verify_student.services.IDVerificationService.user_status')
    def test_retry_until_verification_status_updates(self, user_status_mock, generate_user_certs_mock):
        course_key = 'course-v1:edX+CS101+2017_T2'
        student = UserFactory()

        kwargs = {
            'student': student.id,
            'course_key': course_key,
            'expected_verification_status': IDVerificationAttempt.STATUS.approved
        }

        user_status_mock.side_effect = [
            {'status': 'pending', 'error': '', 'should_display': True},
            {'status': 'approved', 'error': '', 'should_display': True}
        ]

        generate_certificate.apply_async(kwargs=kwargs).get()

        user_status_mock.assert_has_calls([
            call(student),
            call(student)
        ])

        generate_user_certs_mock.assert_called_once_with(
            student=student,
            course_key=CourseKey.from_string(course_key)
        )
