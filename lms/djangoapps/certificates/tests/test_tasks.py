from unittest import TestCase

import ddt
from mock import patch

from lms.djangoapps.certificates.tasks import generate_certificate


@ddt.ddt
class GenerateUserCertificateTest(TestCase):
    @patch('lms.djangoapps.certificates.tasks.generate_user_certificates')
    def test_cert_task(self, generate_user_certs_mock):
        generate_certificate(student='a', course_key='b', otherarg='c', otherotherarg='d')
        generate_user_certs_mock.assert_called_with(student='a', course_key='b', otherarg='c', otherotherarg='d')

    @ddt.data('student', 'course_key')
    def test_cert_task_missing_args(self, missing_arg):
        kwargs = {'student': 'a', 'course_key': 'b', 'otherarg': 'c'}
        del kwargs[missing_arg]
        with self.assertRaisesRegexp(KeyError, missing_arg):
            generate_certificate(**kwargs)
