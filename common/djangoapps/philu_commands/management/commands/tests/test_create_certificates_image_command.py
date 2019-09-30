from __future__ import unicode_literals

from datetime import datetime, timedelta

import mock
from certificates.tests.factories import GeneratedCertificateFactory
from django.core.management import call_command
from django.db.models.signals import post_save
from factory.django import mute_signals
from lms.djangoapps.onboarding.tests.factories import UserFactory
from student.tests.factories import CourseEnrollmentFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


class CreateCertificateImage(SharedModuleStoreTestCase):
    """
        Tests for `create_certificates_image` command.
    """

    @mute_signals(post_save)
    def setUp(self):
        """
        This function is responsible for creating user and courses for every test and mocking the function for tests.
        :return:
        """
        super(CreateCertificateImage, self).setUp()
        self.user = UserFactory()
        self.course = CourseFactory()
        self.course.certificates_display_behavior = "early_with_info"
        patcher = mock.patch(
            'openedx.features.student_certificates.tasks.task_create_certificate_img_and_upload_to_s3.delay')
        self.mock_request = patcher.start()
        self.addCleanup(patcher.stop)

    def test_create_certificates_images_command(self):
        """
        This Test case checks the scenario for creating the certificates images of all of the Generated Certificates.
        """
        certificate_uuid = self._create_certificate_and_get_uuid('honor')
        call_command('create_certificates_image')
        self.mock_request.assert_called_once_with(verify_uuid=certificate_uuid)

    def test_create_certificates_images_command_with_date_argument(self):
        """
        This Test case checks the scenario for creating the certificates images of Generated Certificates after the
        given date.
        """
        certificate_uuid = self._create_certificate_and_get_uuid('honor')
        after_date = (datetime.now() - timedelta(days=1)).strftime("%d/%m/%Y")
        call_command('create_certificates_image', '--after={}'.format(after_date))
        self.mock_request.assert_called_once_with(verify_uuid=certificate_uuid)

    def test_create_certificates_images_command_with_uuid_argument(self):
        """
        This Test case checks the scenario for creating the certificates images of Generated Certificates for the given
        UUID.
        """
        certificate_uuid = self._create_certificate_and_get_uuid('honor')
        call_command('create_certificates_image', '--uuid={}'.format(certificate_uuid))
        self.mock_request.assert_called_once_with(verify_uuid=certificate_uuid)

    def _create_certificate_and_get_uuid(self, enrollment_mode):
        """Simulate that the user has a generated certificate. """
        CourseEnrollmentFactory.create(user=self.user, course_id=self.course.id, mode=enrollment_mode)
        certificate = GeneratedCertificateFactory(
            user=self.user,
            course_id=self.course.id,
            mode=enrollment_mode,
            status="downloadable",
            grade=0.98,
        )
        return certificate.verify_uuid
