"""
Tests for programs celery tasks.
"""
import json
import unittest

from celery.exceptions import MaxRetriesExceededError
import ddt
from django.conf import settings
from django.core.cache import cache
from django.test import override_settings, TestCase
from edx_rest_api_client.client import EdxRestApiClient
from edx_oauth2_provider.tests.factories import ClientFactory
import httpretty
import mock
from provider.constants import CONFIDENTIAL

from lms.djangoapps.certificates.api import MODES
from openedx.core.djangoapps.credentials.tests.mixins import CredentialsApiConfigMixin
from openedx.core.djangoapps.programs.tests import factories
from openedx.core.djangoapps.programs.tests.mixins import ProgramsApiConfigMixin
from openedx.core.djangoapps.programs.tasks.v1 import tasks
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase
from student.tests.factories import UserFactory


TASKS_MODULE = 'openedx.core.djangoapps.programs.tasks.v1.tasks'
UTILS_MODULE = 'openedx.core.djangoapps.programs.utils'


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class GetApiClientTestCase(TestCase, ProgramsApiConfigMixin):
    """
    Test the get_api_client function
    """

    @mock.patch(TASKS_MODULE + '.get_id_token')
    def test_get_api_client(self, mock_get_id_token):
        """
        Ensure the function is making the right API calls based on inputs
        """
        student = UserFactory()
        ClientFactory.create(name='programs')
        api_config = self.create_programs_config(
            internal_service_url='http://foo',
            api_version_number=99,
        )
        mock_get_id_token.return_value = 'test-token'

        api_client = tasks.get_api_client(api_config, student)
        self.assertEqual(mock_get_id_token.call_args[0], (student, 'programs'))
        self.assertEqual(api_client._store['base_url'], 'http://foo/api/v99/')  # pylint: disable=protected-access
        self.assertEqual(api_client._store['session'].auth.token, 'test-token')  # pylint: disable=protected-access


@httpretty.activate
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class GetCompletedProgramsTestCase(ProgramsApiConfigMixin, CacheIsolationTestCase):
    """
    Test the get_completed_programs function
    """
    ENABLED_CACHES = ['default']

    def setUp(self):
        super(GetCompletedProgramsTestCase, self).setUp()

        self.user = UserFactory()
        self.programs_config = self.create_programs_config(cache_ttl=5)

        ClientFactory(name=self.programs_config.OAUTH2_CLIENT_NAME, client_type=CONFIDENTIAL)

        cache.clear()

    def _mock_programs_api(self, data):
        """Helper for mocking out Programs API URLs."""
        self.assertTrue(httpretty.is_enabled(), msg='httpretty must be enabled to mock Programs API calls.')

        url = self.programs_config.internal_api_url.strip('/') + '/programs/'
        body = json.dumps({'results': data})

        httpretty.register_uri(httpretty.GET, url, body=body, content_type='application/json')

    def _assert_num_requests(self, count):
        """DRY helper for verifying request counts."""
        self.assertEqual(len(httpretty.httpretty.latest_requests), count)

    @mock.patch(UTILS_MODULE + '.get_completed_courses')
    def test_get_completed_programs(self, mock_get_completed_courses):
        """
        Verify that completed programs are found, using the cache when possible.
        """
        course_id = 'org/course/run'
        data = [
            factories.Program(
                organizations=[factories.Organization()],
                course_codes=[
                    factories.CourseCode(run_modes=[
                        factories.RunMode(course_key=course_id),
                    ]),
                ]
            ),
        ]
        self._mock_programs_api(data)

        mock_get_completed_courses.return_value = [
            {'course_id': course_id, 'mode': MODES.verified}
        ]

        for _ in range(2):
            result = tasks.get_completed_programs(self.user)
            self.assertEqual(result, [data[0]['id']])

        # Verify that only one request to programs was made (i.e., the cache was hit).
        self._assert_num_requests(1)


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class GetAwardedCertificateProgramsTestCase(TestCase):
    """
    Test the get_awarded_certificate_programs function
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
                'program_id': None,
            },
            'status': 'dummy-status',
            'uuid': 'dummy-uuid',
            'certificate_url': 'http://credentials.edx.org/credentials/dummy-uuid/'
        }
        result.update(**kwargs)
        return result

    @mock.patch(TASKS_MODULE + '.get_user_credentials')
    def test_get_awarded_certificate_programs(self, mock_get_user_credentials):
        """
        Ensure the API is called and results handled correctly.
        """
        student = UserFactory(username='test-username')
        mock_get_user_credentials.return_value = [
            self.make_credential_result(status='awarded', credential={'program_id': 1}),
            self.make_credential_result(status='awarded', credential={'course_id': 2}),
            self.make_credential_result(status='revoked', credential={'program_id': 3}),
        ]

        result = tasks.get_awarded_certificate_programs(student)
        self.assertEqual(mock_get_user_credentials.call_args[0], (student, ))
        self.assertEqual(result, [1])


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
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
            'http://test-server/user_credentials/',
        )

        tasks.award_program_certificate(test_client, test_username, 123)

        expected_body = {
            'username': test_username,
            'credential': {'program_id': 123},
            'attributes': []
        }
        self.assertEqual(json.loads(httpretty.last_request().body), expected_body)


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
@ddt.ddt
@mock.patch(TASKS_MODULE + '.award_program_certificate')
@mock.patch(TASKS_MODULE + '.get_awarded_certificate_programs')
@mock.patch(TASKS_MODULE + '.get_completed_programs')
@override_settings(CREDENTIALS_SERVICE_USERNAME='test-service-username')
class AwardProgramCertificatesTestCase(TestCase, ProgramsApiConfigMixin, CredentialsApiConfigMixin):
    """
    Tests for the 'award_program_certificates' celery task.
    """

    def setUp(self):
        super(AwardProgramCertificatesTestCase, self).setUp()
        self.create_programs_config()
        self.create_credentials_config()
        self.student = UserFactory.create(username='test-student')

        ClientFactory.create(name='programs')
        ClientFactory.create(name='credentials')
        UserFactory.create(username=settings.CREDENTIALS_SERVICE_USERNAME)  # pylint: disable=no-member

    def test_completion_check(
            self,
            mock_get_completed_programs,
            mock_get_awarded_certificate_programs,  # pylint: disable=unused-argument
            mock_award_program_certificate,  # pylint: disable=unused-argument
    ):
        """
        Checks that the Programs API is used correctly to determine completed
        programs.
        """
        tasks.award_program_certificates.delay(self.student.username).get()
        mock_get_completed_programs.assert_called_once_with(self.student)

    @ddt.data(
        ([1], [2, 3]),
        ([], [1, 2, 3]),
        ([1, 2, 3], []),
    )
    @ddt.unpack
    def test_awarding_certs(
            self,
            already_awarded_program_ids,
            expected_awarded_program_ids,
            mock_get_completed_programs,
            mock_get_awarded_certificate_programs,
            mock_award_program_certificate,
    ):
        """
        Checks that the Credentials API is used to award certificates for
        the proper programs.
        """
        mock_get_completed_programs.return_value = [1, 2, 3]
        mock_get_awarded_certificate_programs.return_value = already_awarded_program_ids

        tasks.award_program_certificates.delay(self.student.username).get()

        actual_program_ids = [call[0][2] for call in mock_award_program_certificate.call_args_list]
        self.assertEqual(actual_program_ids, expected_awarded_program_ids)

    @ddt.data(
        ('programs', 'enable_certification'),
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
            mock_get_awarded_certificate_programs,
            mock_award_program_certificate,
    ):
        """
        Checks that the task will be aborted without further action if there
        are no programs for which to award a certificate.
        """
        mock_get_completed_programs.return_value = []
        tasks.award_program_certificates.delay(self.student.username).get()
        self.assertTrue(mock_get_completed_programs.called)
        self.assertFalse(mock_get_awarded_certificate_programs.called)
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
            mock_get_awarded_certificate_programs,
            mock_award_program_certificate,
    ):
        """
        Checks that a single failure to award one of several certificates
        does not cause the entire task to fail.  Also ensures that
        successfully awarded certs are logged as INFO and exceptions
        that arise are logged also.
        """
        mock_get_completed_programs.return_value = [1, 2]
        mock_get_awarded_certificate_programs.side_effect = [[], [2]]
        mock_award_program_certificate.side_effect = self._make_side_effect([Exception('boom'), None])

        with mock.patch(TASKS_MODULE + '.LOGGER.info') as mock_info, \
                mock.patch(TASKS_MODULE + '.LOGGER.exception') as mock_exception:
            tasks.award_program_certificates.delay(self.student.username).get()

        self.assertEqual(mock_award_program_certificate.call_count, 3)
        mock_exception.assert_called_once_with(mock.ANY, 1, self.student.username)
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
        self.assertEqual(mock_get_completed_programs.call_count, 2)

    def test_retry_on_credentials_api_errors(
            self,
            mock_get_completed_programs,
            mock_get_awarded_certificate_programs,
            mock_award_program_certificate,
    ):
        """
        Ensures that any otherwise-unhandled errors that arise while trying
        to get existing program credentials (e.g. network issues or other
        transient API errors) will cause the task to be failed and queued for
        retry.
        """
        mock_get_completed_programs.return_value = [1, 2]
        mock_get_awarded_certificate_programs.return_value = [1]
        mock_get_awarded_certificate_programs.side_effect = self._make_side_effect([Exception('boom'), None])
        tasks.award_program_certificates.delay(self.student.username).get()
        self.assertEqual(mock_get_awarded_certificate_programs.call_count, 2)
        self.assertEqual(mock_award_program_certificate.call_count, 1)
