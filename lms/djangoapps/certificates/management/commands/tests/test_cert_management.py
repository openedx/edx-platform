"""Tests for the resubmit_error_certificates management command. """


from unittest.mock import patch

import ddt
from django.core.management import call_command
from django.core.management.base import CommandError

from common.djangoapps.course_modes.models import CourseMode
from common.djangoapps.student.tests.factories import CourseEnrollmentFactory, UserFactory
from lms.djangoapps.badges.tests.factories import CourseCompleteImageConfigurationFactory
from lms.djangoapps.certificates.data import CertificateStatuses
from lms.djangoapps.certificates.models import GeneratedCertificate
from lms.djangoapps.certificates.tests.factories import GeneratedCertificateFactory
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory


class CertificateManagementTest(ModuleStoreTestCase):
    """
    Base test class for Certificate Management command tests.
    """
    # Override with the command module you wish to test.
    command = 'resubmit_error_certificates'

    def setUp(self):
        super().setUp()
        self.user = UserFactory.create()
        self.courses = [
            CourseFactory.create()
            for __ in range(3)
        ]
        for course in self.courses:
            chapter = ItemFactory.create(parent_location=course.location)
            ItemFactory.create(parent_location=chapter.location, category='sequential', graded=True)
        CourseCompleteImageConfigurationFactory.create()

    def _create_cert(self, course_key, user, status, mode=CourseMode.HONOR):
        """Create a certificate entry. """
        # Enroll the user in the course
        CourseEnrollmentFactory.create(
            user=user,
            course_id=course_key,
            mode=mode
        )

        # Create the certificate
        GeneratedCertificateFactory(
            user=user,
            course_id=course_key,
            status=status
        )

    def _assert_cert_status(self, course_key, user, expected_status):
        """Check the status of a certificate. """
        cert = GeneratedCertificate.eligible_certificates.get(user=user, course_id=course_key)
        assert cert.status == expected_status


@ddt.ddt
class ResubmitErrorCertificatesTest(CertificateManagementTest):
    """Tests for the resubmit_error_certificates management command. """
    ENABLED_SIGNALS = ['course_published']

    def test_resubmit_error_certificate_none_found(self):
        self._create_cert(self.courses[0].id, self.user, CertificateStatuses.downloadable)
        call_command(self.command)
        self._assert_cert_status(self.courses[0].id, self.user, CertificateStatuses.downloadable)

    def test_course_caching(self):
        # Create multiple certificates for the same course
        self._create_cert(self.courses[0].id, UserFactory.create(), CertificateStatuses.error)
        self._create_cert(self.courses[0].id, UserFactory.create(), CertificateStatuses.error)
        self._create_cert(self.courses[0].id, UserFactory.create(), CertificateStatuses.error)

        course_overview = CourseOverviewFactory.create(
            id=self.courses[0].id
        )

        with patch(
            'lms.djangoapps.certificates.management.commands.resubmit_error_certificates.get_course_overview_or_none'
        ) as mock_get_course_overview:
            mock_get_course_overview.return_value = course_overview

            call_command(self.command)

            mock_get_course_overview.assert_called_once()

    def test_invalid_course_key(self):
        invalid_key = "invalid/"
        with self.assertRaisesRegex(CommandError, invalid_key):
            call_command(self.command, course_key_list=[invalid_key])
