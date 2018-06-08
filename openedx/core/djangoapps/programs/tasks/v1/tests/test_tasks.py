"""
Tests for programs celery tasks.
"""
import json
from datetime import datetime
import ddt
import httpretty
import mock
from celery.exceptions import MaxRetriesExceededError
from django.conf import settings
from django.test import override_settings, TestCase
from edx_oauth2_provider.tests.factories import ClientFactory
from edx_rest_api_client import exceptions
from edx_rest_api_client.client import EdxRestApiClient

from lms.djangoapps.certificates.tests.factories import GeneratedCertificateFactory
from openedx.core.djangoapps.catalog.tests.mixins import CatalogIntegrationMixin
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory
from openedx.core.djangoapps.credentials.tests.mixins import CredentialsApiConfigMixin
from openedx.core.djangoapps.programs.tasks.v1 import tasks
from openedx.core.djangoapps.site_configuration.tests.factories import SiteFactory
from openedx.core.djangolib.testing.utils import skip_unless_lms
from student.tests.factories import UserFactory


CREDENTIALS_INTERNAL_SERVICE_URL = 'https://credentials.example.com'
TASKS_MODULE = 'openedx.core.djangoapps.programs.tasks.v1.tasks'


@skip_unless_lms
class GetAwardedCertificateProgramsTestCase(TestCase):
    """
    Test the get_certified_programs function
    """

    def make_credential_result(self, **kwargs):
        """
        Helper to make dummy results from the credentials API
        """
        result = {
            'id': 1,
            'username': 'dummy-username',
            'credential': {
                'credential_id': None,
                'program_uuid': None,
            },
            'status': 'dummy-status',
            'uuid': 'dummy-uuid',
            'certificate_url': 'http://credentials.edx.org/credentials/dummy-uuid/'
        }
        result.update(**kwargs)
        return result

    @mock.patch(TASKS_MODULE + '.get_credentials')
    def test_get_certified_programs(self, mock_get_credentials):
        """
        Ensure the API is called and results handled correctly.
        """
        student = UserFactory(username='test-username')
        mock_get_credentials.return_value = [
            self.make_credential_result(status='awarded', credential={'program_uuid': 1}),
        ]

        result = tasks.get_certified_programs(student)
        self.assertEqual(mock_get_credentials.call_args[0], (student,))
        self.assertEqual(mock_get_credentials.call_args[1], {'credential_type': 'program'})
        self.assertEqual(result, [1])


@skip_unless_lms
class AwardProgramCertificateTestCase(TestCase):
    """
    Test the award_program_certificate function
    """

    @httpretty.activate
    def test_award_program_certificate(self):
        """
        Ensure the correct API call gets made
        """
        test_username = 'test-username'
        test_client = EdxRestApiClient('http://test-server', jwt='test-token')

        httpretty.register_uri(
            httpretty.POST,
            'http://test-server/credentials/',
        )

        tasks.award_program_certificate(test_client, test_username, 123)

        expected_body = {
            'username': test_username,
            'credential': {
                'program_uuid': 123,
                'type': tasks.PROGRAM_CERTIFICATE,
            },
            'attributes': []
        }
        self.assertEqual(json.loads(httpretty.last_request().body), expected_body)


@skip_unless_lms
@ddt.ddt
@mock.patch(TASKS_MODULE + '.award_program_certificate')
@mock.patch(TASKS_MODULE + '.get_certified_programs')
@mock.patch(TASKS_MODULE + '.get_completed_programs')
@override_settings(CREDENTIALS_SERVICE_USERNAME='test-service-username')
class AwardProgramCertificatesTestCase(CatalogIntegrationMixin, CredentialsApiConfigMixin, TestCase):
    """
    Tests for the 'award_program_certificates' celery task.
    """

    def setUp(self):
        super(AwardProgramCertificatesTestCase, self).setUp()
        self.create_credentials_config()
        self.student = UserFactory.create(username='test-student')
        self.site = SiteFactory()

        self.catalog_integration = self.create_catalog_integration()
        ClientFactory.create(name='credentials')
        UserFactory.create(username=settings.CREDENTIALS_SERVICE_USERNAME)  # pylint: disable=no-member

    def test_completion_check(
        self,
        mock_get_completed_programs,
        mock_get_certified_programs,  # pylint: disable=unused-argument
        mock_award_program_certificate,  # pylint: disable=unused-argument
    ):
        """
        Checks that the Programs API is used correctly to determine completed
        programs.
        """
        tasks.award_program_certificates.delay(self.student.username).get()
        mock_get_completed_programs.assert_called(self.site, self.student)

    @ddt.data(
        ([1], [2, 3]),
        ([], [1, 2, 3]),
        ([1, 2, 3], []),
    )
    @ddt.unpack
    def test_awarding_certs(
        self,
        already_awarded_program_uuids,
        expected_awarded_program_uuids,
        mock_get_completed_programs,
        mock_get_certified_programs,
        mock_award_program_certificate,
    ):
        """
        Checks that the Credentials API is used to award certificates for
        the proper programs.
        """
        mock_get_completed_programs.return_value = [1, 2, 3]
        mock_get_certified_programs.return_value = already_awarded_program_uuids

        tasks.award_program_certificates.delay(self.student.username).get()

        actual_program_uuids = [call[0][2] for call in mock_award_program_certificate.call_args_list]
        self.assertEqual(actual_program_uuids, expected_awarded_program_uuids)

    @ddt.data(
        ('credentials', 'enable_learner_issuance'),
    )
    @ddt.unpack
    def test_retry_if_config_disabled(
        self,
        disabled_config_type,
        disabled_config_attribute,
        *mock_helpers
    ):
        """
        Checks that the task is aborted if any relevant api configs are
        disabled.
        """
        getattr(self, 'create_{}_config'.format(disabled_config_type))(**{disabled_config_attribute: False})
        with mock.patch(TASKS_MODULE + '.LOGGER.warning') as mock_warning:
            with self.assertRaises(MaxRetriesExceededError):
                tasks.award_program_certificates.delay(self.student.username).get()
            self.assertTrue(mock_warning.called)
        for mock_helper in mock_helpers:
            self.assertFalse(mock_helper.called)

    def test_abort_if_invalid_username(self, *mock_helpers):
        """
        Checks that the task will be aborted and not retried if the username
        passed was not found, and that an exception is logged.
        """
        with mock.patch(TASKS_MODULE + '.LOGGER.exception') as mock_exception:
            tasks.award_program_certificates.delay('nonexistent-username').get()
            self.assertTrue(mock_exception.called)
        for mock_helper in mock_helpers:
            self.assertFalse(mock_helper.called)

    def test_abort_if_no_completed_programs(
        self,
        mock_get_completed_programs,
        mock_get_certified_programs,
        mock_award_program_certificate,
    ):
        """
        Checks that the task will be aborted without further action if there
        are no programs for which to award a certificate.
        """
        mock_get_completed_programs.return_value = []
        tasks.award_program_certificates.delay(self.student.username).get()
        self.assertTrue(mock_get_completed_programs.called)
        self.assertFalse(mock_get_certified_programs.called)
        self.assertFalse(mock_award_program_certificate.called)

    def _make_side_effect(self, side_effects):
        """
        DRY helper.  Returns a side effect function for use with mocks that
        will be called multiple times, permitting Exceptions to be raised
        (or not) in a specified order.

        See Also:
            http://www.voidspace.org.uk/python/mock/examples.html#multiple-calls-with-different-effects
            http://www.voidspace.org.uk/python/mock/mock.html#mock.Mock.side_effect

        """

        def side_effect(*_a):  # pylint: disable=missing-docstring
            if side_effects:
                exc = side_effects.pop(0)
                if exc:
                    raise exc
            return mock.DEFAULT

        return side_effect

    def test_continue_awarding_certs_if_error(
        self,
        mock_get_completed_programs,
        mock_get_certified_programs,
        mock_award_program_certificate,
    ):
        """
        Checks that a single failure to award one of several certificates
        does not cause the entire task to fail.  Also ensures that
        successfully awarded certs are logged as INFO and warning is logged
        for failed requests if there are retries available.
        """
        mock_get_completed_programs.return_value = [1, 2]
        mock_get_certified_programs.side_effect = [[], [2]]
        mock_award_program_certificate.side_effect = self._make_side_effect([Exception('boom'), None])

        with mock.patch(TASKS_MODULE + '.LOGGER.info') as mock_info, \
                mock.patch(TASKS_MODULE + '.LOGGER.warning') as mock_warning:
            tasks.award_program_certificates.delay(self.student.username).get()

        self.assertEqual(mock_award_program_certificate.call_count, 3)
        mock_warning.assert_called_once_with(
            'Failed to award certificate for program {uuid} to user {username}.'.format(
                uuid=1,
                username=self.student.username)
        )
        mock_info.assert_any_call(mock.ANY, 1, self.student.username)
        mock_info.assert_any_call(mock.ANY, 2, self.student.username)

    def test_retry_on_programs_api_errors(
        self,
        mock_get_completed_programs,
        *_mock_helpers  # pylint: disable=unused-argument
    ):
        """
        Ensures that any otherwise-unhandled errors that arise while trying
        to get completed programs (e.g. network issues or other
        transient API errors) will cause the task to be failed and queued for
        retry.
        """
        mock_get_completed_programs.side_effect = self._make_side_effect([Exception('boom'), None])
        tasks.award_program_certificates.delay(self.student.username).get()
        self.assertEqual(mock_get_completed_programs.call_count, 3)

    def test_retry_on_credentials_api_errors(
        self,
        mock_get_completed_programs,
        mock_get_certified_programs,
        mock_award_program_certificate,
    ):
        """
        Ensures that any otherwise-unhandled errors that arise while trying
        to get existing program credentials (e.g. network issues or other
        transient API errors) will cause the task to be failed and queued for
        retry.
        """
        mock_get_completed_programs.return_value = [1, 2]
        mock_get_certified_programs.return_value = [1]
        mock_get_certified_programs.side_effect = self._make_side_effect([Exception('boom'), None])
        tasks.award_program_certificates.delay(self.student.username).get()
        self.assertEqual(mock_get_certified_programs.call_count, 2)
        self.assertEqual(mock_award_program_certificate.call_count, 1)

    def test_no_retry_on_credentials_api_not_found_errors(
        self,
        mock_get_completed_programs,
        mock_get_certified_programs,
        mock_award_program_certificate,
    ):
        mock_get_completed_programs.return_value = [1, 2]
        mock_get_certified_programs.side_effect = [[], [2]]
        mock_award_program_certificate.side_effect = self._make_side_effect(
            [exceptions.HttpNotFoundError(), None]
        )

        tasks.award_program_certificates.delay(self.student.username).get()

        self.assertEqual(mock_award_program_certificate.call_count, 2)


@skip_unless_lms
class PostCourseCertificateTestCase(TestCase):
    """
    Test the award_program_certificate function
    """

    def setUp(self):
        self.student = UserFactory.create(username='test-student')
        self.course = CourseOverviewFactory.create(
            self_paced=True  # Any option to allow the certificate to be viewable for the course
        )
        self.certificate = GeneratedCertificateFactory(
            user=self.student,
            mode='verified',
            course_id=self.course.id,
            status='downloadable'
        )

    @httpretty.activate
    def test_post_course_certificate(self):
        """
        Ensure the correct API call gets made
        """
        test_client = EdxRestApiClient('http://test-server', jwt='test-token')

        httpretty.register_uri(
            httpretty.POST,
            'http://test-server/credentials/',
        )

        visible_date = datetime.now()

        tasks.post_course_certificate(test_client, self.student.username, self.certificate, visible_date)

        expected_body = {
            'username': self.student.username,
            'status': 'awarded',
            'credential': {
                'course_run_key': str(self.certificate.course_id),
                'mode': self.certificate.mode,
                'type': tasks.COURSE_CERTIFICATE,
            },
            'attributes': [{
                'name': 'visible_date',
                'value': visible_date.strftime('%Y-%m-%dT%H:%M:%SZ')  # text representation of date
            }]
        }
        self.assertEqual(json.loads(httpretty.last_request().body), expected_body)


@skip_unless_lms
@mock.patch(TASKS_MODULE + '.post_course_certificate')
@override_settings(CREDENTIALS_SERVICE_USERNAME='test-service-username')
class AwardCourseCertificatesTestCase(CredentialsApiConfigMixin, TestCase):
    """
    Test the award_course_certificate celery task
    """

    def setUp(self):
        super(AwardCourseCertificatesTestCase, self).setUp()

        self.course = CourseOverviewFactory.create(
            self_paced=True  # Any option to allow the certificate to be viewable for the course
        )
        self.student = UserFactory.create(username='test-student')
        # Instantiate the Certificate first so that the config doesn't execute issuance
        self.certificate = GeneratedCertificateFactory.create(
            user=self.student,
            mode='verified',
            course_id=self.course.id,
            status='downloadable'
        )

        self.create_credentials_config()
        self.site = SiteFactory()

        ClientFactory.create(name='credentials')
        UserFactory.create(username=settings.CREDENTIALS_SERVICE_USERNAME)

    def test_award_course_certificates(self, mock_post_course_certificate):
        """
        Tests the API POST method is called with appropriate params when configured properly
        """
        tasks.award_course_certificate.delay(self.student.username, self.course.id).get()
        call_args, _ = mock_post_course_certificate.call_args
        self.assertEqual(call_args[1], self.student.username)
        self.assertEqual(call_args[2], self.certificate)

    def test_award_course_cert_not_called_if_disabled(self, mock_post_course_certificate):
        """
        Test that the post method is never called if the config is disabled
        """
        self.create_credentials_config(enabled=False)
        with mock.patch(TASKS_MODULE + '.LOGGER.warning') as mock_warning:
            with self.assertRaises(MaxRetriesExceededError):
                tasks.award_course_certificate.delay(self.student.username, self.course.id).get()
        self.assertTrue(mock_warning.called)
        self.assertFalse(mock_post_course_certificate.called)

    def test_award_course_cert_not_called_if_user_not_found(self, mock_post_course_certificate):
        """
        Test that the post method is never called if the user isn't found by username
        """
        with mock.patch(TASKS_MODULE + '.LOGGER.exception') as mock_exception:
            # Use a random username here since this user won't be found in the DB
            tasks.award_course_certificate.delay('random_username', self.course.id).get()
        self.assertTrue(mock_exception.called)
        self.assertFalse(mock_post_course_certificate.called)

    def test_award_course_cert_not_called_if_certificate_not_found(self, mock_post_course_certificate):
        """
        Test that the post method is never called if the certificate doesn't exist for the user and course
        """
        self.certificate.delete()
        with mock.patch(TASKS_MODULE + '.LOGGER.exception') as mock_exception:
            tasks.award_course_certificate.delay(self.student.username, self.course.id).get()
        self.assertTrue(mock_exception.called)
        self.assertFalse(mock_post_course_certificate.called)

    def test_award_course_cert_not_called_if_course_overview_not_found(self, mock_post_course_certificate):
        """
        Test that the post method is never called if the CourseOverview isn't found
        """
        self.course.delete()
        with mock.patch(TASKS_MODULE + '.LOGGER.exception') as mock_exception:
            # Use the certificate course id here since the course will be deleted
            tasks.award_course_certificate.delay(self.student.username, self.certificate.course_id).get()
        self.assertTrue(mock_exception.called)
        self.assertFalse(mock_post_course_certificate.called)

    def test_award_course_cert_not_called_if_certificated_not_verified_mode(self, mock_post_course_certificate):
        """
        Test that the post method is never called if the GeneratedCertificate is an 'audit' cert
        """
        # Temporarily disable the config so the signal isn't handled from .save
        self.create_credentials_config(enabled=False)
        self.certificate.mode = 'audit'
        self.certificate.save()
        self.create_credentials_config()

        tasks.award_course_certificate.delay(self.student.username, self.certificate.course_id).get()
        self.assertFalse(mock_post_course_certificate.called)
