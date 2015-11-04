"""Tests for the certificates panel of the instructor dash. """
import contextlib
import ddt
import mock
import json

from nose.plugins.attrib import attr
from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from django.conf import settings
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from config_models.models import cache
from courseware.tests.factories import GlobalStaffFactory, InstructorFactory, UserFactory
from certificates.tests.factories import GeneratedCertificateFactory
from certificates.models import CertificateGenerationConfiguration, CertificateStatuses
from certificates import api as certs_api


@attr('shard_1')
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
        patched = 'instructor.views.instructor_dashboard.certs_api.example_certificates_status'
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


@attr('shard_1')
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

        # Enable certificate generation
        self.certificate_exception_data = [
            dict(
                created="Wednesday, October 28, 2015",
                notes="Test Notes for Test Certificate Exception",
                user_email='',
                user_id='',
                user_name=unicode(self.user.username)
            ),
        ]

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

    def test_certificate_exception_added_successfully(self):
        """
        Test certificates exception addition api endpoint returns success status and updated certificate exception data
        when called with valid course key and certificate exception data
        """
        self.client.login(username=self.global_staff.username, password='test')
        url = reverse(
            'create_certificate_exception',
            kwargs={'course_id': unicode(self.course.id), 'white_list_student': ''}
        )

        response = self.client.post(
            url,
            data=json.dumps(self.certificate_exception_data),
            content_type='application/json'
        )

        # Assert successful request processing
        self.assertEqual(response.status_code, 200)
        res_json = json.loads(response.content)

        # Assert Request was successful
        self.assertTrue(res_json['success'])

        # Assert Success Message
        self.assertEqual(res_json['message'], u'Students added to Certificate white list successfully')

        # Assert Certificate Exception Updated data
        certificate_exception = json.loads(res_json['data'])[0]
        self.assertEqual(certificate_exception['user_email'], self.user.email)
        self.assertEqual(certificate_exception['user_name'], self.user.username)
        self.assertEqual(certificate_exception['user_id'], self.user.id)  # pylint: disable=no-member

    def test_certificate_exception_invalid_username_error(self):
        """
        Test certificates exception addition api endpoint returns failure when called with
        invalid username.
        """
        invalid_user = 'test_invalid_user_name'
        self.certificate_exception_data[0].update({'user_name': invalid_user})

        self.client.login(username=self.global_staff.username, password='test')
        url = reverse(
            'create_certificate_exception',
            kwargs={'course_id': unicode(self.course.id), 'white_list_student': ''}
        )

        response = self.client.post(
            url,
            data=json.dumps(self.certificate_exception_data),
            content_type='application/json')

        # Assert 400 status code in response
        self.assertEqual(response.status_code, 400)
        res_json = json.loads(response.content)

        # Assert Request not successful
        self.assertFalse(res_json['success'])

        # Assert Error Message
        self.assertEqual(
            res_json['message'],
            u'Student (username/email={user}) does not exist'.format(user=invalid_user)
        )

    def test_certificate_exception_missing_username_and_email_error(self):
        """
        Test certificates exception addition api endpoint returns failure when called with
        missing username/email.
        """
        self.certificate_exception_data[0].update({'user_name': '', 'user_email': ''})

        self.client.login(username=self.global_staff.username, password='test')
        url = reverse(
            'create_certificate_exception',
            kwargs={'course_id': unicode(self.course.id), 'white_list_student': ''}
        )

        response = self.client.post(
            url,
            data=json.dumps(self.certificate_exception_data),
            content_type='application/json')

        # Assert 400 status code in response
        self.assertEqual(response.status_code, 400)
        res_json = json.loads(response.content)

        # Assert Request not successful
        self.assertFalse(res_json['success'])

        # Assert Error Message
        self.assertEqual(
            res_json['message'],
            u'Student username/email is required.'
        )

    def test_certificate_exception_duplicate_user_error(self):
        """
        Test certificates exception addition api endpoint returns failure when called with
        username/email that already exists in 'CertificateWhitelist' table.
        """

        self.client.login(username=self.global_staff.username, password='test')
        url = reverse(
            'create_certificate_exception',
            kwargs={'course_id': unicode(self.course.id), 'white_list_student': ''}
        )

        self.client.post(
            url,
            data=json.dumps(self.certificate_exception_data),
            content_type='application/json'
        )

        # Make some request again to simulate duplicate user scenario
        response = self.client.post(
            url,
            data=json.dumps(self.certificate_exception_data),
            content_type='application/json'
        )

        # Assert 400 status code in response
        self.assertEqual(response.status_code, 400)
        res_json = json.loads(response.content)

        # Assert Request not successful
        self.assertFalse(res_json['success'])

        user = self.certificate_exception_data[0]['user_name']
        # Assert Error Message
        self.assertEqual(
            res_json['message'],
            u"Student (username/email={user_id} already in certificate exception  list)".format(user_id=user)
        )

    def test_certificate_exception_same_user_in_two_different_courses(self):
        """
        Test certificates exception addition api endpoint in scenario when same
        student is added to two different courses.
        """

        self.client.login(username=self.global_staff.username, password='test')

        url_course1 = reverse(
            'create_certificate_exception',
            kwargs={'course_id': unicode(self.course.id), 'white_list_student': ''}
        )

        response = self.client.post(
            url_course1,
            data=json.dumps(self.certificate_exception_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        res_json = json.loads(response.content)
        self.assertTrue(res_json['success'])

        course2 = CourseFactory.create()
        url_course2 = reverse(
            'create_certificate_exception',
            kwargs={'course_id': unicode(course2.id), 'white_list_student': ''}
        )

        # add certificate exception for same user in a different course
        self.client.post(
            url_course2,
            data=json.dumps(self.certificate_exception_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        res_json = json.loads(response.content)
        self.assertTrue(res_json['success'])

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
