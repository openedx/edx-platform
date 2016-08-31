"""Tests for the certificates panel of the instructor dash. """
import contextlib
import ddt
import mock
import json
import pytz

from datetime import datetime, timedelta

from nose.plugins.attrib import attr
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.test.utils import override_settings
from django.conf import settings

from mock import patch, PropertyMock

from course_modes.models import CourseMode
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from config_models.models import cache
from courseware.tests.factories import GlobalStaffFactory, InstructorFactory, UserFactory
from certificates.tests.factories import GeneratedCertificateFactory, CertificateWhitelistFactory, \
    CertificateInvalidationFactory
from certificates.models import CertificateGenerationConfiguration, CertificateStatuses, CertificateWhitelist, \
    GeneratedCertificate, CertificateInvalidation
from certificates import api as certs_api
from student.models import CourseEnrollment
from django.core.files.uploadedfile import SimpleUploadedFile
import io


@attr(shard=1)
@ddt.ddt
class CertificatesInstructorDashTest(SharedModuleStoreTestCase):
    """Tests for the certificate panel of the instructor dash. """

    ERROR_REASON = "An error occurred!"
    DOWNLOAD_URL = "http://www.example.com/abcd123/cert.pdf"

    @classmethod
    def setUpClass(cls):
        super(CertificatesInstructorDashTest, cls).setUpClass()
        cls.course = CourseFactory.create()
        cls.url = reverse(
            'instructor_dashboard',
            kwargs={'course_id': unicode(cls.course.id)}
        )

    def setUp(self):
        super(CertificatesInstructorDashTest, self).setUp()
        self.global_staff = GlobalStaffFactory()
        self.instructor = InstructorFactory(course_key=self.course.id)

        # Need to clear the cache for model-based configuration
        cache.clear()

        # Enable the certificate generation feature
        CertificateGenerationConfiguration.objects.create(enabled=True)

    def test_visible_only_to_global_staff(self):
        # Instructors don't see the certificates section
        self.client.login(username=self.instructor.username, password="test")
        self._assert_certificates_visible(False)

        # Global staff can see the certificates section
        self.client.login(username=self.global_staff.username, password="test")
        self._assert_certificates_visible(True)

    def test_visible_only_when_feature_flag_enabled(self):
        # Disable the feature flag
        CertificateGenerationConfiguration.objects.create(enabled=False)
        cache.clear()

        # Now even global staff can't see the certificates section
        self.client.login(username=self.global_staff.username, password="test")
        self._assert_certificates_visible(False)

    @ddt.data("started", "error", "success")
    def test_show_certificate_status(self, status):
        self.client.login(username=self.global_staff.username, password="test")
        with self._certificate_status("honor", status):
            self._assert_certificate_status("honor", status)

    def test_show_enabled_button(self):
        self.client.login(username=self.global_staff.username, password="test")

        # Initially, no example certs are generated, so
        # the enable button should be disabled
        self._assert_enable_certs_button_is_disabled()

        with self._certificate_status("honor", "success"):
            # Certs are disabled for the course, so the enable button should be shown
            self._assert_enable_certs_button(True)

            # Enable certificates for the course
            certs_api.set_cert_generation_enabled(self.course.id, True)

            # Now the "disable" button should be shown
            self._assert_enable_certs_button(False)

    def test_can_disable_even_after_failure(self):
        self.client.login(username=self.global_staff.username, password="test")

        with self._certificate_status("honor", "error"):
            # When certs are disabled for a course, then don't allow them
            # to be enabled if certificate generation doesn't complete successfully
            certs_api.set_cert_generation_enabled(self.course.id, False)
            self._assert_enable_certs_button_is_disabled()

            # However, if certificates are already enabled, allow them
            # to be disabled even if an error has occurred
            certs_api.set_cert_generation_enabled(self.course.id, True)
            self._assert_enable_certs_button(False)

    @mock.patch.dict(settings.FEATURES, {'CERTIFICATES_HTML_VIEW': True})
    def test_show_enabled_button_for_html_certs(self):
        """
        Tests `Enable Student-Generated Certificates` button is enabled
        and `Generate Example Certificates` button is not available if
        course has Web/HTML certificates view enabled.
        """
        self.course.cert_html_view_enabled = True
        self.course.save()
        self.store.update_item(self.course, self.global_staff.id)  # pylint: disable=no-member
        self.client.login(username=self.global_staff.username, password="test")
        response = self.client.get(self.url)
        self.assertContains(response, 'Enable Student-Generated Certificates')
        self.assertContains(response, 'enable-certificates-submit')
        self.assertNotContains(response, 'Generate Example Certificates')

    @mock.patch.dict(settings.FEATURES, {'CERTIFICATES_HTML_VIEW': True})
    def test_buttons_for_html_certs_in_self_paced_course(self):
        """
        Tests `Enable Student-Generated Certificates` button is enabled
        and `Generate Certificates` button is not available if
        course has Web/HTML certificates view enabled on a self paced course.
        """
        self.course.cert_html_view_enabled = True
        self.course.save()
        self.store.update_item(self.course, self.global_staff.id)  # pylint: disable=no-member
        self.client.login(username=self.global_staff.username, password="test")
        response = self.client.get(self.url)
        self.assertContains(response, 'Enable Student-Generated Certificates')
        self.assertContains(response, 'enable-certificates-submit')
        self.assertNotContains(response, 'Generate Certificates')
        self.assertNotContains(response, 'btn-start-generating-certificates')

    def _assert_certificates_visible(self, is_visible):
        """Check that the certificates section is visible on the instructor dash. """
        response = self.client.get(self.url)
        if is_visible:
            self.assertContains(response, "Student-Generated Certificates")
        else:
            self.assertNotContains(response, "Student-Generated Certificates")

    @contextlib.contextmanager
    def _certificate_status(self, description, status):
        """Configure the certificate status by mocking the certificates API. """
        patched = 'lms.djangoapps.instructor.views.instructor_dashboard.certs_api.example_certificates_status'
        with mock.patch(patched) as certs_api_status:
            cert_status = [{
                'description': description,
                'status': status
            }]

            if status == 'error':
                cert_status[0]['error_reason'] = self.ERROR_REASON
            if status == 'success':
                cert_status[0]['download_url'] = self.DOWNLOAD_URL

            certs_api_status.return_value = cert_status
            yield

    def _assert_certificate_status(self, cert_name, expected_status):
        """Check the certificate status display on the instructor dash. """
        response = self.client.get(self.url)

        if expected_status == 'started':
            expected = 'Generating example {name} certificate'.format(name=cert_name)
            self.assertContains(response, expected)
        elif expected_status == 'error':
            expected = self.ERROR_REASON
            self.assertContains(response, expected)
        elif expected_status == 'success':
            expected = self.DOWNLOAD_URL
            self.assertContains(response, expected)
        else:
            self.fail("Invalid certificate status: {status}".format(status=expected_status))

    def _assert_enable_certs_button_is_disabled(self):
        """Check that the "enable student-generated certificates" button is disabled. """
        response = self.client.get(self.url)
        expected_html = '<button class="is-disabled" disabled>Enable Student-Generated Certificates</button>'
        self.assertContains(response, expected_html)

    def _assert_enable_certs_button(self, is_enabled):
        """Check whether the button says "enable" or "disable" cert generation. """
        response = self.client.get(self.url)
        expected_html = (
            'Enable Student-Generated Certificates' if is_enabled
            else 'Disable Student-Generated Certificates'
        )
        self.assertContains(response, expected_html)


@attr(shard=1)
@override_settings(CERT_QUEUE='certificates')
@ddt.ddt
class CertificatesInstructorApiTest(SharedModuleStoreTestCase):
    """Tests for the certificates end-points in the instructor dash API. """
    @classmethod
    def setUpClass(cls):
        super(CertificatesInstructorApiTest, cls).setUpClass()
        cls.course = CourseFactory.create()

    def setUp(self):
        super(CertificatesInstructorApiTest, self).setUp()
        self.global_staff = GlobalStaffFactory()
        self.instructor = InstructorFactory(course_key=self.course.id)
        self.user = UserFactory()
        CourseEnrollment.enroll(self.user, self.course.id)

        # Enable certificate generation
        cache.clear()
        CertificateGenerationConfiguration.objects.create(enabled=True)

    @ddt.data('generate_example_certificates', 'enable_certificate_generation')
    def test_allow_only_global_staff(self, url_name):
        url = reverse(url_name, kwargs={'course_id': self.course.id})

        # Instructors do not have access
        self.client.login(username=self.instructor.username, password='test')
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)

        # Global staff have access
        self.client.login(username=self.global_staff.username, password='test')
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

    def test_generate_example_certificates(self):
        self.client.login(username=self.global_staff.username, password='test')
        url = reverse(
            'generate_example_certificates',
            kwargs={'course_id': unicode(self.course.id)}
        )
        response = self.client.post(url)

        # Expect a redirect back to the instructor dashboard
        self._assert_redirects_to_instructor_dash(response)

        # Expect that certificate generation started
        # Cert generation will fail here because XQueue isn't configured,
        # but the status should at least not be None.
        status = certs_api.example_certificates_status(self.course.id)
        self.assertIsNot(status, None)

    @ddt.data(True, False)
    def test_enable_certificate_generation(self, is_enabled):
        self.client.login(username=self.global_staff.username, password='test')
        url = reverse(
            'enable_certificate_generation',
            kwargs={'course_id': unicode(self.course.id)}
        )
        params = {'certificates-enabled': 'true' if is_enabled else 'false'}
        response = self.client.post(url, data=params)

        # Expect a redirect back to the instructor dashboard
        self._assert_redirects_to_instructor_dash(response)

        # Expect that certificate generation is now enabled for the course
        actual_enabled = certs_api.cert_generation_enabled(self.course.id)
        self.assertEqual(is_enabled, actual_enabled)

    def _assert_redirects_to_instructor_dash(self, response):
        """Check that the response redirects to the certificates section. """
        expected_redirect = reverse(
            'instructor_dashboard',
            kwargs={'course_id': unicode(self.course.id)}
        )
        expected_redirect += '#view-certificates'
        self.assertRedirects(response, expected_redirect)

    def test_certificate_generation_api_without_global_staff(self):
        """
        Test certificates generation api endpoint returns permission denied if
        user who made the request is not member of global staff.
        """
        user = UserFactory.create()
        self.client.login(username=user.username, password='test')
        url = reverse(
            'start_certificate_generation',
            kwargs={'course_id': unicode(self.course.id)}
        )

        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)

        self.client.login(username=self.instructor.username, password='test')
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)

    def test_certificate_generation_api_with_global_staff(self):
        """
        Test certificates generation api endpoint returns success status when called with
        valid course key
        """
        self.client.login(username=self.global_staff.username, password='test')
        url = reverse(
            'start_certificate_generation',
            kwargs={'course_id': unicode(self.course.id)}
        )

        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        res_json = json.loads(response.content)
        self.assertIsNotNone(res_json['message'])
        self.assertIsNotNone(res_json['task_id'])

    def test_certificate_regeneration_success(self):
        """
        Test certificate regeneration is successful when accessed with 'certificate_statuses'
        present in GeneratedCertificate table.
        """

        # Create a generated Certificate of some user with status 'downloadable'
        GeneratedCertificateFactory.create(
            user=self.user,
            course_id=self.course.id,
            status=CertificateStatuses.downloadable,
            mode='honor'
        )

        # Login the client and access the url with 'certificate_statuses'
        self.client.login(username=self.global_staff.username, password='test')
        url = reverse('start_certificate_regeneration', kwargs={'course_id': unicode(self.course.id)})
        response = self.client.post(url, data={'certificate_statuses': [CertificateStatuses.downloadable]})

        # Assert 200 status code in response
        self.assertEqual(response.status_code, 200)
        res_json = json.loads(response.content)

        # Assert request is successful
        self.assertTrue(res_json['success'])

        # Assert success message
        self.assertEqual(
            res_json['message'],
            u'Certificate regeneration task has been started. You can view the status of the generation task in '
            u'the "Pending Tasks" section.'
        )

    @patch(
        'lms.djangoapps.grades.new.course_grade.CourseGrade.summary',
        PropertyMock(return_value={'grade': 'Pass', 'percent': 0.75})
    )
    @override_settings(AUDIT_CERT_CUTOFF_DATE=datetime.now(pytz.UTC) - timedelta(days=1))
    @ddt.data(
        ('verified', 'ID Verified', True),
        ('unverified', 'Not ID Verified', False)
    )
    @ddt.unpack
    def test_verified_users_with_audit_certs(self, expected_cert_status, verification_output, user_verified):
        """
        Test that `verified_users_with_audit_certs` option regenerates certificate for verified users with audit
        certificates get certificate.

        Scenario:
            User enrolled in course as audit,
            User passed the course as audit so they have `audit_passing` certificate status,
            User switched to verified mode and is ID verified,
            Regenerate certificates for `verified_users_with_audit_certs` is run,
            Modified certificate status is `verified` if user is ID verified otherwise `unverified`.
        """
        # Check that user is enrolled in audit mode.
        enrollment = CourseEnrollment.get_enrollment(self.user, self.course.id)
        self.assertEqual(enrollment.mode, CourseMode.AUDIT)

        # Generate certificate for user and check that user has a audit passing certificate.
        with patch('student.models.CourseEnrollment.refund_cutoff_date') as cutoff_date:
            cutoff_date.return_value = datetime.now(pytz.UTC) - timedelta(minutes=5)
            cert_status = certs_api.generate_user_certificates(student=self.user, course_key=self.course.id, course=self.course)
            self.assertEqual(cert_status, CertificateStatuses.audit_passing)

        # Update user enrollment mode to verified mode.
        enrollment.update_enrollment(mode='verified')
        self.assertEqual(enrollment.mode, CourseMode.VERIFIED)

        with patch(
            'lms.djangoapps.verify_student.models.SoftwareSecurePhotoVerification.user_is_verified'
        ) as user_verify:
            user_verify.return_value = user_verified

            # Login the client and access the url with 'certificate_statuses'
            self.client.login(username=self.global_staff.username, password='test')
            url = reverse('start_certificate_regeneration', kwargs={'course_id': unicode(self.course.id)})
            response = self.client.post(url, data={'certificate_statuses': ['verified_users_with_audit_certs']})

            # Assert 200 status code in response
            self.assertEqual(response.status_code, 200)
            res_json = json.loads(response.content)

            # Assert request is successful
            self.assertTrue(res_json['success'])

            # Assert success message
            self.assertEqual(
                res_json['message'],
                u'Certificate regeneration task has been started. You can view the status of the generation task in '
                u'the "Pending Tasks" section.'
            )
            # Check user has a not audit passing certificate now.
            cert = certs_api.get_certificate_for_user(self.user.username, self.course.id)
            self.assertNotEqual(cert['status'], CertificateStatuses.audit_passing)
            self.assertEqual(cert['status'], expected_cert_status)

    def test_certificate_regeneration_error(self):
        """
        Test certificate regeneration errors out when accessed with either empty list of 'certificate_statuses' or
        the 'certificate_statuses' that are not present in GeneratedCertificate table.
        """
        # Create a dummy course and GeneratedCertificate with the same status as the one we will use to access
        # 'start_certificate_regeneration' but their error message should be displayed as GeneratedCertificate
        # belongs to a different course
        dummy_course = CourseFactory.create()
        GeneratedCertificateFactory.create(
            user=self.user,
            course_id=dummy_course.id,
            status=CertificateStatuses.generating,
            mode='honor'
        )

        # Login the client and access the url without 'certificate_statuses'
        self.client.login(username=self.global_staff.username, password='test')
        url = reverse('start_certificate_regeneration', kwargs={'course_id': unicode(self.course.id)})
        response = self.client.post(url)

        # Assert 400 status code in response
        self.assertEqual(response.status_code, 400)
        res_json = json.loads(response.content)

        # Assert Error Message
        self.assertEqual(
            res_json['message'],
            u'Please select one or more certificate statuses that require certificate regeneration.'
        )

        # Access the url passing 'certificate_statuses' that are not present in db
        url = reverse('start_certificate_regeneration', kwargs={'course_id': unicode(self.course.id)})
        response = self.client.post(url, data={'certificate_statuses': [CertificateStatuses.generating]})

        # Assert 400 status code in response
        self.assertEqual(response.status_code, 400)
        res_json = json.loads(response.content)

        # Assert Error Message
        self.assertEqual(res_json['message'], u'Please select certificate statuses from the list only.')


@attr(shard=1)
@override_settings(CERT_QUEUE='certificates')
@ddt.ddt
class CertificateExceptionViewInstructorApiTest(SharedModuleStoreTestCase):
    """Tests for the generate certificates end-points in the instructor dash API. """
    @classmethod
    def setUpClass(cls):
        super(CertificateExceptionViewInstructorApiTest, cls).setUpClass()
        cls.course = CourseFactory.create()

    def setUp(self):
        super(CertificateExceptionViewInstructorApiTest, self).setUp()
        self.global_staff = GlobalStaffFactory()
        self.instructor = InstructorFactory(course_key=self.course.id)
        self.user = UserFactory()
        self.user2 = UserFactory()
        CourseEnrollment.enroll(self.user, self.course.id)
        CourseEnrollment.enroll(self.user2, self.course.id)
        self.url = reverse('certificate_exception_view', kwargs={'course_id': unicode(self.course.id)})

        certificate_white_list_item = CertificateWhitelistFactory.create(
            user=self.user2,
            course_id=self.course.id,
        )

        self.certificate_exception = dict(
            created="",
            notes="Test Notes for Test Certificate Exception",
            user_email='',
            user_id='',
            user_name=unicode(self.user.username)
        )

        self.certificate_exception_in_db = dict(
            id=certificate_white_list_item.id,
            user_name=certificate_white_list_item.user.username,
            notes=certificate_white_list_item.notes,
            user_email=certificate_white_list_item.user.email,
            user_id=certificate_white_list_item.user.id,
        )

        # Enable certificate generation
        cache.clear()
        CertificateGenerationConfiguration.objects.create(enabled=True)
        self.client.login(username=self.global_staff.username, password='test')

    def test_certificate_exception_added_successfully(self):
        """
        Test certificates exception addition api endpoint returns success status and updated certificate exception data
        when called with valid course key and certificate exception data
        """
        response = self.client.post(
            self.url,
            data=json.dumps(self.certificate_exception),
            content_type='application/json'
        )
        # Assert successful request processing
        self.assertEqual(response.status_code, 200)
        certificate_exception = json.loads(response.content)

        # Assert Certificate Exception Updated data
        self.assertEqual(certificate_exception['user_email'], self.user.email)
        self.assertEqual(certificate_exception['user_name'], self.user.username)
        self.assertEqual(certificate_exception['user_id'], self.user.id)  # pylint: disable=no-member

    def test_certificate_exception_invalid_username_error(self):
        """
        Test certificates exception addition api endpoint returns failure when called with
        invalid username.
        """
        invalid_user = 'test_invalid_user_name'
        self.certificate_exception.update({'user_name': invalid_user})
        response = self.client.post(
            self.url,
            data=json.dumps(self.certificate_exception),
            content_type='application/json'
        )

        # Assert 400 status code in response
        self.assertEqual(response.status_code, 400)
        res_json = json.loads(response.content)

        # Assert Request not successful
        self.assertFalse(res_json['success'])

        # Assert Error Message
        self.assertEqual(
            res_json['message'],
            u"{user} does not exist in the LMS. Please check your spelling and retry.".format(user=invalid_user)
        )

    def test_certificate_exception_missing_username_and_email_error(self):
        """
        Test certificates exception addition api endpoint returns failure when called with
        missing username/email.
        """
        self.certificate_exception.update({'user_name': '', 'user_email': ''})
        response = self.client.post(
            self.url,
            data=json.dumps(self.certificate_exception),
            content_type='application/json'
        )

        # Assert 400 status code in response
        self.assertEqual(response.status_code, 400)
        res_json = json.loads(response.content)

        # Assert Request not successful
        self.assertFalse(res_json['success'])

        # Assert Error Message
        self.assertEqual(
            res_json['message'],
            u'Student username/email field is required and can not be empty. '
            u'Kindly fill in username/email and then press "Add to Exception List" button.'
        )

    def test_certificate_exception_duplicate_user_error(self):
        """
        Test certificates exception addition api endpoint returns failure when called with
        username/email that already exists in 'CertificateWhitelist' table.
        """
        response = self.client.post(
            self.url,
            data=json.dumps(self.certificate_exception_in_db),
            content_type='application/json'
        )

        # Assert 400 status code in response
        self.assertEqual(response.status_code, 400)
        res_json = json.loads(response.content)

        # Assert Request not successful
        self.assertFalse(res_json['success'])

        user = self.certificate_exception_in_db['user_name']
        # Assert Error Message
        self.assertEqual(
            res_json['message'],
            u"Student (username/email={user_name}) already in certificate exception list.".format(user_name=user)
        )

    def test_certificate_exception_same_user_in_two_different_courses(self):
        """
        Test certificates exception addition api endpoint in scenario when same
        student is added to two different courses.
        """
        response = self.client.post(
            self.url,
            data=json.dumps(self.certificate_exception),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        certificate_exception = json.loads(response.content)

        # Assert Certificate Exception Updated data
        self.assertEqual(certificate_exception['user_email'], self.user.email)
        self.assertEqual(certificate_exception['user_name'], self.user.username)
        self.assertEqual(certificate_exception['user_id'], self.user.id)  # pylint: disable=no-member

        course2 = CourseFactory.create()
        url_course2 = reverse(
            'certificate_exception_view',
            kwargs={'course_id': unicode(course2.id)}
        )

        # add certificate exception for same user in a different course
        self.client.post(
            url_course2,
            data=json.dumps(self.certificate_exception),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        certificate_exception = json.loads(response.content)

        # Assert Certificate Exception Updated data
        self.assertEqual(certificate_exception['user_email'], self.user.email)
        self.assertEqual(certificate_exception['user_name'], self.user.username)
        self.assertEqual(certificate_exception['user_id'], self.user.id)  # pylint: disable=no-member

    def test_certificate_exception_user_not_enrolled_error(self):
        """
        Test certificates exception addition api endpoint returns failure when called with
        username/email that is not enrolled in the given course.
        """
        # Un-enroll student from the course
        CourseEnrollment.unenroll(self.user, self.course.id)
        response = self.client.post(
            self.url,
            data=json.dumps(self.certificate_exception),
            content_type='application/json'
        )

        # Assert 400 status code in response
        self.assertEqual(response.status_code, 400)
        res_json = json.loads(response.content)

        # Assert Request not successful
        self.assertFalse(res_json['success'])

        # Assert Error Message
        self.assertEqual(
            res_json['message'],
            "{user} is not enrolled in this course. Please check your spelling and retry.".format(
                user=self.certificate_exception['user_name']
            )
        )

    def test_certificate_exception_removed_successfully(self):
        """
        Test certificates exception removal api endpoint returns success status
        when called with valid course key and certificate exception id
        """
        GeneratedCertificateFactory.create(
            user=self.user2,
            course_id=self.course.id,
            status=CertificateStatuses.downloadable,
            grade='1.0'
        )
        response = self.client.post(
            self.url,
            data=json.dumps(self.certificate_exception_in_db),
            content_type='application/json',
            REQUEST_METHOD='DELETE'
        )
        # Assert successful request processing
        self.assertEqual(response.status_code, 204)

        # Verify that certificate exception successfully removed from CertificateWhitelist and GeneratedCertificate
        with self.assertRaises(ObjectDoesNotExist):
            CertificateWhitelist.objects.get(user=self.user2, course_id=self.course.id)
            GeneratedCertificate.eligible_certificates.get(
                user=self.user2, course_id=self.course.id, status__not=CertificateStatuses.unavailable
            )

    def test_remove_certificate_exception_invalid_request_error(self):
        """
        Test certificates exception removal api endpoint returns error
        when called without certificate exception id
        """
        # Try to delete certificate exception without passing valid data
        response = self.client.post(
            self.url,
            data='Test Invalid data',
            content_type='application/json',
            REQUEST_METHOD='DELETE'
        )
        # Assert error on request
        self.assertEqual(response.status_code, 400)

        res_json = json.loads(response.content)

        # Assert Request not successful
        self.assertFalse(res_json['success'])
        # Assert Error Message
        self.assertEqual(
            res_json['message'],
            u"The record is not in the correct format. Please add a valid username or email address."
        )

    def test_remove_certificate_exception_non_existing_error(self):
        """
        Test certificates exception removal api endpoint returns error
        when called with non existing certificate exception id
        """
        response = self.client.post(
            self.url,
            data=json.dumps(self.certificate_exception),
            content_type='application/json',
            REQUEST_METHOD='DELETE'
        )
        # Assert error on request
        self.assertEqual(response.status_code, 400)

        res_json = json.loads(response.content)

        # Assert Request not successful
        self.assertFalse(res_json['success'])
        # Assert Error Message
        self.assertEqual(
            res_json['message'],
            u"Certificate exception (user={user}) does not exist in certificate white list. "
            u"Please refresh the page and try again.".format(user=self.certificate_exception['user_name'])
        )


@attr(shard=1)
@override_settings(CERT_QUEUE='certificates')
@ddt.ddt
class GenerateCertificatesInstructorApiTest(SharedModuleStoreTestCase):
    """Tests for the generate certificates end-points in the instructor dash API. """
    @classmethod
    def setUpClass(cls):
        super(GenerateCertificatesInstructorApiTest, cls).setUpClass()
        cls.course = CourseFactory.create()

    def setUp(self):
        super(GenerateCertificatesInstructorApiTest, self).setUp()
        self.global_staff = GlobalStaffFactory()
        self.instructor = InstructorFactory(course_key=self.course.id)
        self.user = UserFactory()
        CourseEnrollment.enroll(self.user, self.course.id)
        certificate_exception = CertificateWhitelistFactory.create(
            user=self.user,
            course_id=self.course.id,
        )

        self.certificate_exception = dict(
            id=certificate_exception.id,
            user_name=certificate_exception.user.username,
            notes=certificate_exception.notes,
            user_email=certificate_exception.user.email,
            user_id=certificate_exception.user.id,
        )

        # Enable certificate generation
        cache.clear()
        CertificateGenerationConfiguration.objects.create(enabled=True)
        self.client.login(username=self.global_staff.username, password='test')

    def test_generate_certificate_exceptions_all_students(self):
        """
        Test generate certificates exceptions api endpoint returns success
        when called with existing certificate exception
        """
        url = reverse(
            'generate_certificate_exceptions',
            kwargs={'course_id': unicode(self.course.id), 'generate_for': 'all'}
        )

        response = self.client.post(
            url,
            content_type='application/json'
        )
        # Assert Success
        self.assertEqual(response.status_code, 200)

        res_json = json.loads(response.content)

        # Assert Request is successful
        self.assertTrue(res_json['success'])
        # Assert Message
        self.assertEqual(
            res_json['message'],
            u"Certificate generation started for white listed students."
        )

    def test_generate_certificate_exceptions_whitelist_not_generated(self):
        """
        Test generate certificates exceptions api endpoint returns success
        when calling with new certificate exception.
        """
        url = reverse(
            'generate_certificate_exceptions',
            kwargs={'course_id': unicode(self.course.id), 'generate_for': 'new'}
        )

        response = self.client.post(
            url,
            content_type='application/json'
        )

        # Assert Success
        self.assertEqual(response.status_code, 200)

        res_json = json.loads(response.content)

        # Assert Request is successful
        self.assertTrue(res_json['success'])
        # Assert Message
        self.assertEqual(
            res_json['message'],
            u"Certificate generation started for white listed students."
        )

    def test_generate_certificate_exceptions_generate_for_incorrect_value(self):
        """
        Test generate certificates exceptions api endpoint returns error
        when calling with generate_for without 'new' or 'all' value.
        """
        url = reverse(
            'generate_certificate_exceptions',
            kwargs={'course_id': unicode(self.course.id), 'generate_for': ''}
        )

        response = self.client.post(
            url,
            content_type='application/json'
        )

        # Assert Failure
        self.assertEqual(response.status_code, 400)

        res_json = json.loads(response.content)

        # Assert Request is not successful
        self.assertFalse(res_json['success'])
        # Assert Message
        self.assertEqual(
            res_json['message'],
            u'Invalid data, generate_for must be "new" or "all".'
        )


@attr(shard=1)
@ddt.ddt
class TestCertificatesInstructorApiBulkWhiteListExceptions(SharedModuleStoreTestCase):
    """
    Test Bulk certificates white list exceptions from csv file
    """
    @classmethod
    def setUpClass(cls):
        super(TestCertificatesInstructorApiBulkWhiteListExceptions, cls).setUpClass()
        cls.course = CourseFactory.create()
        cls.url = reverse('generate_bulk_certificate_exceptions',
                          kwargs={'course_id': cls.course.id})

    def setUp(self):
        super(TestCertificatesInstructorApiBulkWhiteListExceptions, self).setUp()
        self.global_staff = GlobalStaffFactory()
        self.enrolled_user_1 = UserFactory(
            username='TestStudent1',
            email='test_student1@example.com',
            first_name='Enrolled',
            last_name='Student'
        )
        self.enrolled_user_2 = UserFactory(
            username='TestStudent2',
            email='test_student2@example.com',
            first_name='Enrolled',
            last_name='Student'
        )

        self.not_enrolled_student = UserFactory(
            username='NotEnrolledStudent',
            email='nonenrolled@test.com',
            first_name='NotEnrolled',
            last_name='Student'
        )
        CourseEnrollment.enroll(self.enrolled_user_1, self.course.id)
        CourseEnrollment.enroll(self.enrolled_user_2, self.course.id)

        # Global staff can see the certificates section
        self.client.login(username=self.global_staff.username, password="test")

    def test_create_white_list_exception_record(self):
        """
        Happy path test to create a single new white listed record
        """
        csv_content = "test_student1@example.com,dummy_notes\n" \
                      "test_student2@example.com,dummy_notes"
        data = self.upload_file(csv_content=csv_content)
        self.assertEquals(len(data['general_errors']), 0)
        self.assertEquals(len(data['row_errors']['data_format_error']), 0)
        self.assertEquals(len(data['row_errors']['user_not_exist']), 0)
        self.assertEquals(len(data['row_errors']['user_already_white_listed']), 0)
        self.assertEquals(len(data['row_errors']['user_not_enrolled']), 0)
        self.assertEquals(len(data['success']), 2)
        self.assertEquals(len(CertificateWhitelist.objects.all()), 2)

    def test_invalid_data_format_in_csv(self):
        """
        Try uploading a CSV file with invalid data formats and verify the errors.
        """
        csv_content = "test_student1@example.com,test,1,USA\n" \
                      "test_student2@example.com,test,1"

        data = self.upload_file(csv_content=csv_content)
        self.assertEquals(len(data['row_errors']['data_format_error']), 2)
        self.assertEquals(len(data['general_errors']), 0)
        self.assertEquals(len(data['success']), 0)
        self.assertEquals(len(CertificateWhitelist.objects.all()), 0)

    def test_file_upload_type_not_csv(self):
        """
        Try uploading some non-CSV file e.g. .JPG file and verify that it is rejected
        """
        uploaded_file = SimpleUploadedFile("temp.jpg", io.BytesIO(b"some initial binary data: \x00\x01").read())
        response = self.client.post(self.url, {'students_list': uploaded_file})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertNotEquals(len(data['general_errors']), 0)
        self.assertEquals(data['general_errors'][0], 'Make sure that the file you upload is in CSV format with '
                                                     'no extraneous characters or rows.')

    def test_bad_file_upload_type(self):
        """
        Try uploading CSV file with invalid binary data and verify that it is rejected
        """
        uploaded_file = SimpleUploadedFile("temp.csv", io.BytesIO(b"some initial binary data: \x00\x01").read())
        response = self.client.post(self.url, {'students_list': uploaded_file})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertNotEquals(len(data['general_errors']), 0)
        self.assertEquals(data['general_errors'][0], 'Could not read uploaded file.')

    def test_invalid_email_in_csv(self):
        """
        Test failure case of a poorly formatted email field
        """
        csv_content = "test_student.example.com,dummy_notes"

        data = self.upload_file(csv_content=csv_content)
        self.assertEquals(len(data['row_errors']['user_not_exist']), 1)
        self.assertEquals(len(data['success']), 0)
        self.assertEquals(len(CertificateWhitelist.objects.all()), 0)

    def test_csv_user_not_enrolled(self):
        """
        If the user is not enrolled in the course then there should be a user_not_enrolled error.
        """
        csv_content = "nonenrolled@test.com,dummy_notes"

        data = self.upload_file(csv_content=csv_content)
        self.assertEquals(len(data['row_errors']['user_not_enrolled']), 1)
        self.assertEquals(len(data['general_errors']), 0)
        self.assertEquals(len(data['success']), 0)

    def test_certificate_exception_already_exist(self):
        """
        Test error if existing user is already in certificates exception list.
        """
        CertificateWhitelist.objects.create(
            user=self.enrolled_user_1,
            course_id=self.course.id,
            whitelist=True,
            notes=''
        )
        csv_content = "test_student1@example.com,dummy_notes"
        data = self.upload_file(csv_content=csv_content)
        self.assertEquals(len(data['row_errors']['user_already_white_listed']), 1)
        self.assertEquals(len(data['general_errors']), 0)
        self.assertEquals(len(data['success']), 0)
        self.assertEquals(len(CertificateWhitelist.objects.all()), 1)

    def test_csv_file_not_attached(self):
        """
        Test when the user does not attach a file
        """
        csv_content = "test_student1@example.com,dummy_notes\n" \
                      "test_student2@example.com,dummy_notes"

        uploaded_file = SimpleUploadedFile("temp.csv", csv_content)

        response = self.client.post(self.url, {'file_not_found': uploaded_file})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEquals(len(data['general_errors']), 1)
        self.assertEquals(len(data['success']), 0)

    def upload_file(self, csv_content):
        """
        Upload a csv file.
        :return json data
        """
        uploaded_file = SimpleUploadedFile("temp.csv", csv_content)
        response = self.client.post(self.url, {'students_list': uploaded_file})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        return data


@attr(shard=1)
@ddt.ddt
class CertificateInvalidationViewTests(SharedModuleStoreTestCase):
    """
    Test certificate invalidation view.
    """
    @classmethod
    def setUpClass(cls):
        super(CertificateInvalidationViewTests, cls).setUpClass()
        cls.course = CourseFactory.create()
        cls.url = reverse('certificate_invalidation_view',
                          kwargs={'course_id': cls.course.id})
        cls.notes = "Test notes."

    def setUp(self):
        super(CertificateInvalidationViewTests, self).setUp()
        self.global_staff = GlobalStaffFactory()
        self.enrolled_user_1 = UserFactory(
            username='TestStudent1',
            email='test_student1@example.com',
            first_name='Enrolled',
            last_name='Student',
        )
        self.enrolled_user_2 = UserFactory(
            username='TestStudent2',
            email='test_student2@example.com',
            first_name='Enrolled',
            last_name='Student',
        )

        self.not_enrolled_student = UserFactory(
            username='NotEnrolledStudent',
            email='nonenrolled@test.com',
            first_name='NotEnrolled',
            last_name='Student',
        )
        CourseEnrollment.enroll(self.enrolled_user_1, self.course.id)
        CourseEnrollment.enroll(self.enrolled_user_2, self.course.id)

        self.generated_certificate = GeneratedCertificateFactory.create(
            user=self.enrolled_user_1,
            course_id=self.course.id,
            status=CertificateStatuses.downloadable,
            mode='honor',
        )

        self.certificate_invalidation_data = dict(
            user=self.enrolled_user_1.username,
            notes=self.notes,
        )

        # Global staff can see the certificates section
        self.client.login(username=self.global_staff.username, password="test")

    def test_invalidate_certificate(self):
        """
        Test user can invalidate a generated certificate.
        """
        response = self.client.post(
            self.url,
            data=json.dumps(self.certificate_invalidation_data),
            content_type='application/json',
        )
        # Assert successful request processing
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)

        # Assert Certificate Exception Updated data
        self.assertEqual(result['user'], self.enrolled_user_1.username)
        self.assertEqual(result['invalidated_by'], self.global_staff.username)
        self.assertEqual(result['notes'], self.notes)

        # Verify that CertificateInvalidation record has been created in the database i.e. no DoesNotExist error
        try:
            CertificateInvalidation.objects.get(
                generated_certificate=self.generated_certificate,
                invalidated_by=self.global_staff,
                notes=self.notes,
                active=True,
            )
        except ObjectDoesNotExist:
            self.fail("The certificate is not invalidated.")

        # Validate generated certificate was invalidated
        generated_certificate = GeneratedCertificate.eligible_certificates.get(
            user=self.enrolled_user_1,
            course_id=self.course.id,
        )
        self.assertFalse(generated_certificate.is_valid())

    def test_missing_username_and_email_error(self):
        """
        Test error message if user name or email is missing.
        """
        self.certificate_invalidation_data.update({'user': ''})
        response = self.client.post(
            self.url,
            data=json.dumps(self.certificate_invalidation_data),
            content_type='application/json',
        )

        # Assert 400 status code in response
        self.assertEqual(response.status_code, 400)
        res_json = json.loads(response.content)

        # Assert Error Message
        self.assertEqual(
            res_json['message'],
            u'Student username/email field is required and can not be empty. '
            u'Kindly fill in username/email and then press "Invalidate Certificate" button.',
        )

    def test_invalid_user_name_error(self):
        """
        Test error message if invalid user name is given.
        """
        invalid_user = "test_invalid_user_name"

        self.certificate_invalidation_data.update({"user": invalid_user})

        response = self.client.post(
            self.url,
            data=json.dumps(self.certificate_invalidation_data),
            content_type='application/json',
        )

        # Assert 400 status code in response
        self.assertEqual(response.status_code, 400)
        res_json = json.loads(response.content)

        # Assert Error Message
        self.assertEqual(
            res_json['message'],
            u"{user} does not exist in the LMS. Please check your spelling and retry.".format(user=invalid_user),
        )

    def test_user_not_enrolled_error(self):
        """
        Test error message if user is not enrolled in the course.
        """
        self.certificate_invalidation_data.update({"user": self.not_enrolled_student.username})

        response = self.client.post(
            self.url,
            data=json.dumps(self.certificate_invalidation_data),
            content_type='application/json',
        )

        # Assert 400 status code in response
        self.assertEqual(response.status_code, 400)
        res_json = json.loads(response.content)

        # Assert Error Message
        self.assertEqual(
            res_json['message'],
            u"{user} is not enrolled in this course. Please check your spelling and retry.".format(
                user=self.not_enrolled_student.username,
            ),
        )

    def test_no_generated_certificate_error(self):
        """
        Test error message if there is no generated certificate for the student.
        """
        self.certificate_invalidation_data.update({"user": self.enrolled_user_2.username})

        response = self.client.post(
            self.url,
            data=json.dumps(self.certificate_invalidation_data),
            content_type='application/json',
        )

        # Assert 400 status code in response
        self.assertEqual(response.status_code, 400)
        res_json = json.loads(response.content)

        # Assert Error Message
        self.assertEqual(
            res_json['message'],
            u"The student {student} does not have certificate for the course {course}. "
            u"Kindly verify student username/email and the selected course are correct and try again.".format(
                student=self.enrolled_user_2.username,
                course=self.course.number,
            ),
        )

    def test_certificate_already_invalid_error(self):
        """
        Test error message if certificate for the student is already invalid.
        """
        # Invalidate user certificate
        self.generated_certificate.invalidate()

        response = self.client.post(
            self.url,
            data=json.dumps(self.certificate_invalidation_data),
            content_type='application/json',
        )

        # Assert 400 status code in response
        self.assertEqual(response.status_code, 400)
        res_json = json.loads(response.content)

        # Assert Error Message
        self.assertEqual(
            res_json['message'],
            u"Certificate for student {user} is already invalid, kindly verify that certificate "
            u"was generated for this student and then proceed.".format(
                user=self.enrolled_user_1.username,
            ),
        )

    def test_duplicate_certificate_invalidation_error(self):
        """
        Test error message if certificate invalidation for the student is already present.
        """
        CertificateInvalidationFactory.create(
            generated_certificate=self.generated_certificate,
            invalidated_by=self.global_staff,
        )
        # Invalidate user certificate
        self.generated_certificate.invalidate()

        response = self.client.post(
            self.url,
            data=json.dumps(self.certificate_invalidation_data),
            content_type='application/json',
        )

        # Assert 400 status code in response
        self.assertEqual(response.status_code, 400)
        res_json = json.loads(response.content)

        # Assert Error Message
        self.assertEqual(
            res_json['message'],
            u"Certificate of {user} has already been invalidated. Please check your spelling and retry.".format(
                user=self.enrolled_user_1.username,
            ),
        )

    def test_remove_certificate_invalidation(self):
        """
        Test that user can remove certificate invalidation.
        """
        # Invalidate user certificate
        self.generated_certificate.invalidate()

        CertificateInvalidationFactory.create(
            generated_certificate=self.generated_certificate,
            invalidated_by=self.global_staff,
        )

        response = self.client.post(
            self.url,
            data=json.dumps(self.certificate_invalidation_data),
            content_type='application/json',
            REQUEST_METHOD='DELETE'
        )

        # Assert 204 status code in response
        self.assertEqual(response.status_code, 204)

        # Verify that certificate invalidation successfully removed from database
        with self.assertRaises(ObjectDoesNotExist):
            CertificateInvalidation.objects.get(
                generated_certificate=self.generated_certificate,
                invalidated_by=self.global_staff,
                active=True,
            )

    def test_remove_certificate_invalidation_error(self):
        """
        Test error message if certificate invalidation does not exists.
        """
        # Invalidate user certificate
        self.generated_certificate.invalidate()

        response = self.client.post(
            self.url,
            data=json.dumps(self.certificate_invalidation_data),
            content_type='application/json',
            REQUEST_METHOD='DELETE'
        )

        # Assert 400 status code in response
        self.assertEqual(response.status_code, 400)
        res_json = json.loads(response.content)

        # Assert Error Message
        self.assertEqual(
            res_json['message'],
            u"Certificate Invalidation does not exist, Please refresh the page and try again.",
        )
