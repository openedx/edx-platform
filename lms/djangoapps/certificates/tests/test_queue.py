# -*- coding: utf-8 -*-
"""Tests for the XQueue certificates interface. """
from contextlib import contextmanager
from datetime import datetime, timedelta
import ddt
import json
from mock import patch, Mock
from nose.plugins.attrib import attr

from django.test import TestCase
from django.test.utils import override_settings
import freezegun
import pytz

from course_modes.models import CourseMode
from opaque_keys.edx.locator import CourseLocator
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from student.tests.factories import UserFactory, CourseEnrollmentFactory
from xmodule.modulestore.tests.factories import CourseFactory


# It is really unfortunate that we are using the XQueue client
# code from the capa library.  In the future, we should move this
# into a shared library.  We import it here so we can mock it
# and verify that items are being correctly added to the queue
# in our `XQueueCertInterface` implementation.
from capa.xqueue_interface import XQueueInterface

from certificates.models import (
    ExampleCertificateSet,
    ExampleCertificate,
    GeneratedCertificate,
    CertificateStatuses,
)
from certificates.queue import XQueueCertInterface
from certificates.tests.factories import CertificateWhitelistFactory, GeneratedCertificateFactory
from lms.djangoapps.verify_student.tests.factories import SoftwareSecurePhotoVerificationFactory


@ddt.ddt
@attr('shard_1')
@override_settings(CERT_QUEUE='certificates')
class XQueueCertInterfaceAddCertificateTest(ModuleStoreTestCase):
    """Test the "add to queue" operation of the XQueue interface. """

    def setUp(self):
        super(XQueueCertInterfaceAddCertificateTest, self).setUp()
        self.user = UserFactory.create()
        self.course = CourseFactory.create()
        self.enrollment = CourseEnrollmentFactory(
            user=self.user,
            course_id=self.course.id,
            is_active=True,
            mode="honor",
        )
        self.xqueue = XQueueCertInterface()
        self.user_2 = UserFactory.create()
        SoftwareSecurePhotoVerificationFactory.create(user=self.user_2, status='approved')

    def test_add_cert_callback_url(self):
        with patch('courseware.grades.grade', Mock(return_value={'grade': 'Pass', 'percent': 0.75})):
            with patch.object(XQueueInterface, 'send_to_queue') as mock_send:
                mock_send.return_value = (0, None)
                self.xqueue.add_cert(self.user, self.course.id)

        # Verify that the task was sent to the queue with the correct callback URL
        self.assertTrue(mock_send.called)
        __, kwargs = mock_send.call_args_list[0]
        actual_header = json.loads(kwargs['header'])
        self.assertIn('https://edx.org/update_certificate?key=', actual_header['lms_callback_url'])

    def test_no_create_action_in_queue_for_html_view_certs(self):
        """
        Tests there is no certificate create message in the queue if generate_pdf is False
        """
        with patch('courseware.grades.grade', Mock(return_value={'grade': 'Pass', 'percent': 0.75})):
            with patch.object(XQueueInterface, 'send_to_queue') as mock_send:
                self.xqueue.add_cert(self.user, self.course.id, generate_pdf=False)

        # Verify that add_cert method does not add message to queue
        self.assertFalse(mock_send.called)
        certificate = GeneratedCertificate.eligible_certificates.get(user=self.user, course_id=self.course.id)
        self.assertEqual(certificate.status, CertificateStatuses.downloadable)
        self.assertIsNotNone(certificate.verify_uuid)

    @ddt.data('honor', 'audit')
    @override_settings(AUDIT_CERT_CUTOFF_DATE=datetime.now(pytz.UTC) - timedelta(days=1))
    def test_add_cert_with_honor_certificates(self, mode):
        """Test certificates generations for honor and audit modes."""
        template_name = 'certificate-template-{id.org}-{id.course}.pdf'.format(
            id=self.course.id
        )
        mock_send = self.add_cert_to_queue(mode)
        if CourseMode.is_eligible_for_certificate(mode):
            self.assert_certificate_generated(mock_send, mode, template_name)
        else:
            self.assert_ineligible_certificate_generated(mock_send, mode)

    @ddt.data('credit', 'verified')
    def test_add_cert_with_verified_certificates(self, mode):
        """Test if enrollment mode is verified or credit along with valid
        software-secure verification than verified certificate should be generated.
        """
        template_name = 'certificate-template-{id.org}-{id.course}-verified.pdf'.format(
            id=self.course.id
        )

        mock_send = self.add_cert_to_queue(mode)
        self.assert_certificate_generated(mock_send, 'verified', template_name)

    def test_ineligible_cert_whitelisted(self):
        """Test that audit mode students can receive a certificate if they are whitelisted."""
        # Enroll as audit
        CourseEnrollmentFactory(
            user=self.user_2,
            course_id=self.course.id,
            is_active=True,
            mode='audit'
        )
        # Whitelist student
        CertificateWhitelistFactory(course_id=self.course.id, user=self.user_2)

        # Generate certs
        with patch('courseware.grades.grade', Mock(return_value={'grade': 'Pass', 'percent': 0.75})):
            with patch.object(XQueueInterface, 'send_to_queue') as mock_send:
                mock_send.return_value = (0, None)
                self.xqueue.add_cert(self.user_2, self.course.id)

        # Assert cert generated correctly
        self.assertTrue(mock_send.called)
        certificate = GeneratedCertificate.certificate_for_student(self.user_2, self.course.id)
        self.assertIsNotNone(certificate)
        self.assertEqual(certificate.mode, 'audit')

    def add_cert_to_queue(self, mode):
        """
        Dry method for course enrollment and adding request to
        queue. Returns a mock object containing information about the
        `XQueueInterface.send_to_queue` method, which can be used in other
        assertions.
        """
        CourseEnrollmentFactory(
            user=self.user_2,
            course_id=self.course.id,
            is_active=True,
            mode=mode,
        )
        with patch('courseware.grades.grade', Mock(return_value={'grade': 'Pass', 'percent': 0.75})):
            with patch.object(XQueueInterface, 'send_to_queue') as mock_send:
                mock_send.return_value = (0, None)
                self.xqueue.add_cert(self.user_2, self.course.id)
                return mock_send

    def assert_certificate_generated(self, mock_send, expected_mode, expected_template_name):
        """
        Assert that a certificate was generated with the correct mode and
        template type.
        """
        # Verify that the task was sent to the queue with the correct callback URL
        self.assertTrue(mock_send.called)
        __, kwargs = mock_send.call_args_list[0]

        actual_header = json.loads(kwargs['header'])
        self.assertIn('https://edx.org/update_certificate?key=', actual_header['lms_callback_url'])

        body = json.loads(kwargs['body'])
        self.assertIn(expected_template_name, body['template_pdf'])

        certificate = GeneratedCertificate.eligible_certificates.get(user=self.user_2, course_id=self.course.id)
        self.assertEqual(certificate.mode, expected_mode)

    def assert_ineligible_certificate_generated(self, mock_send, expected_mode):
        """
        Assert that an ineligible certificate was generated with the
        correct mode.
        """
        # Ensure the certificate was not generated
        self.assertFalse(mock_send.called)

        certificate = GeneratedCertificate.objects.get(  # pylint: disable=no-member
            user=self.user_2,
            course_id=self.course.id
        )

        self.assertIn(certificate.status, (CertificateStatuses.audit_passing, CertificateStatuses.audit_notpassing))
        self.assertEqual(certificate.mode, expected_mode)

    @ddt.data(
        (CertificateStatuses.restricted, False),
        (CertificateStatuses.deleting, False),
        (CertificateStatuses.generating, True),
        (CertificateStatuses.unavailable, True),
        (CertificateStatuses.deleted, True),
        (CertificateStatuses.error, True),
        (CertificateStatuses.notpassing, True),
        (CertificateStatuses.downloadable, True),
        (CertificateStatuses.auditing, True),
    )
    @ddt.unpack
    def test_add_cert_statuses(self, status, should_generate):
        """
        Test that certificates can or cannot be generated with the given
        certificate status.
        """
        with patch('certificates.queue.certificate_status_for_student', Mock(return_value={'status': status})):
            mock_send = self.add_cert_to_queue('verified')
            if should_generate:
                self.assertTrue(mock_send.called)
            else:
                self.assertFalse(mock_send.called)

    @ddt.data(
        # Eligible and should stay that way
        (
            CertificateStatuses.downloadable,
            datetime.now(pytz.UTC) - timedelta(days=2),
            'Pass',
            CertificateStatuses.generating
        ),
        # Ensure that certs in the wrong state can be fixed by regeneration
        (
            CertificateStatuses.downloadable,
            datetime.now(pytz.UTC) - timedelta(hours=1),
            'Pass',
            CertificateStatuses.audit_passing
        ),
        # Ineligible and should stay that way
        (
            CertificateStatuses.audit_passing,
            datetime.now(pytz.UTC) - timedelta(hours=1),
            'Pass',
            CertificateStatuses.audit_passing
        ),
        # As above
        (
            CertificateStatuses.audit_notpassing,
            datetime.now(pytz.UTC) - timedelta(hours=1),
            'Pass',
            CertificateStatuses.audit_passing
        ),
        # As above
        (
            CertificateStatuses.audit_notpassing,
            datetime.now(pytz.UTC) - timedelta(hours=1),
            None,
            CertificateStatuses.audit_notpassing
        ),
    )
    @ddt.unpack
    @override_settings(AUDIT_CERT_CUTOFF_DATE=datetime.now(pytz.UTC) - timedelta(days=1))
    def test_regen_audit_certs_eligibility(self, status, created_date, grade, expected_status):
        """
        Test that existing audit certificates remain eligible even if cert
        generation is re-run.
        """
        # Create an existing audit enrollment and certificate
        CourseEnrollmentFactory(
            user=self.user_2,
            course_id=self.course.id,
            is_active=True,
            mode=CourseMode.AUDIT,
        )
        with freezegun.freeze_time(created_date):
            GeneratedCertificateFactory(
                user=self.user_2,
                course_id=self.course.id,
                grade='1.0',
                status=status,
                mode=GeneratedCertificate.MODES.audit,
            )

        # Run grading/cert generation again
        with patch('courseware.grades.grade', Mock(return_value={'grade': grade, 'percent': 0.75})):
            with patch.object(XQueueInterface, 'send_to_queue') as mock_send:
                mock_send.return_value = (0, None)
                self.xqueue.add_cert(self.user_2, self.course.id)

        self.assertEqual(
            GeneratedCertificate.objects.get(user=self.user_2, course_id=self.course.id).status,  # pylint: disable=no-member
            expected_status
        )


@attr('shard_1')
@override_settings(CERT_QUEUE='certificates')
class XQueueCertInterfaceExampleCertificateTest(TestCase):
    """Tests for the XQueue interface for certificate generation. """

    COURSE_KEY = CourseLocator(org='test', course='test', run='test')

    TEMPLATE = 'test.pdf'
    DESCRIPTION = 'test'
    ERROR_MSG = 'Kaboom!'

    def setUp(self):
        super(XQueueCertInterfaceExampleCertificateTest, self).setUp()
        self.xqueue = XQueueCertInterface()

    def test_add_example_cert(self):
        cert = self._create_example_cert()
        with self._mock_xqueue() as mock_send:
            self.xqueue.add_example_cert(cert)

        # Verify that the correct payload was sent to the XQueue
        self._assert_queue_task(mock_send, cert)

        # Verify the certificate status
        self.assertEqual(cert.status, ExampleCertificate.STATUS_STARTED)

    def test_add_example_cert_error(self):
        cert = self._create_example_cert()
        with self._mock_xqueue(success=False):
            self.xqueue.add_example_cert(cert)

        # Verify the error status of the certificate
        self.assertEqual(cert.status, ExampleCertificate.STATUS_ERROR)
        self.assertIn(self.ERROR_MSG, cert.error_reason)

    def _create_example_cert(self):
        """Create an example certificate. """
        cert_set = ExampleCertificateSet.objects.create(course_key=self.COURSE_KEY)
        return ExampleCertificate.objects.create(
            example_cert_set=cert_set,
            description=self.DESCRIPTION,
            template=self.TEMPLATE
        )

    @contextmanager
    def _mock_xqueue(self, success=True):
        """Mock the XQueue method for sending a task to the queue. """
        with patch.object(XQueueInterface, 'send_to_queue') as mock_send:
            mock_send.return_value = (0, None) if success else (1, self.ERROR_MSG)
            yield mock_send

    def _assert_queue_task(self, mock_send, cert):
        """Check that the task was added to the queue. """
        expected_header = {
            'lms_key': cert.access_key,
            'lms_callback_url': 'https://edx.org/update_example_certificate?key={key}'.format(key=cert.uuid),
            'queue_name': 'certificates'
        }

        expected_body = {
            'action': 'create',
            'username': cert.uuid,
            'name': u'John Doë',
            'course_id': unicode(self.COURSE_KEY),
            'template_pdf': 'test.pdf',
            'example_certificate': True
        }

        self.assertTrue(mock_send.called)

        __, kwargs = mock_send.call_args_list[0]
        actual_header = json.loads(kwargs['header'])
        actual_body = json.loads(kwargs['body'])

        self.assertEqual(expected_header, actual_header)
        self.assertEqual(expected_body, actual_body)
