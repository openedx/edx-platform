"""
Test the enterprise support APIs.
"""
import json
import unittest

import ddt
import httpretty
import mock
from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.test.utils import override_settings

from openedx.core.djangolib.testing.utils import CacheIsolationTestCase
from openedx.features.enterprise_support.api import (
    ConsentApiClient,
    ConsentApiServiceClient,
    consent_needed_for_course,
    data_sharing_consent_required,
    EnterpriseApiClient,
    EnterpriseApiServiceClient,
    enterprise_customer_for_request,
    get_dashboard_consent_notification,
    get_enterprise_consent_url,
)
from openedx.features.enterprise_support.tests.mixins.enterprise import EnterpriseServiceMockMixin
from openedx.features.enterprise_support.utils import get_cache_key
from student.tests.factories import UserFactory


class MockEnrollment(mock.MagicMock):
    """
    Mock object for an enrollment which has a consistent string representation
    suitable for use in ddt parameters.
    """
    def __repr__(self):
        return '<MockEnrollment course_id={}>'.format(getattr(self, 'course_id', None))


@ddt.ddt
@override_settings(ENABLE_ENTERPRISE_INTEGRATION=True)
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class TestEnterpriseApi(EnterpriseServiceMockMixin, CacheIsolationTestCase):
    """
    Test enterprise support APIs.
    """
    ENABLED_CACHES = ['default']

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory.create(
            username=settings.ENTERPRISE_SERVICE_WORKER_USERNAME,
            email='ent_worker@example.com',
            password='password123',
        )
        super(TestEnterpriseApi, cls).setUpTestData()

    def _assert_api_service_client(self, api_client, mocked_jwt_builder):
        """
        Verify that the provided api client uses the enterprise service user to generate
        JWT token for auth.
        """
        mocked_jwt_builder.return_value.build_token.return_value = 'test-token'
        enterprise_service_user = User.objects.get(username=settings.ENTERPRISE_SERVICE_WORKER_USERNAME)
        enterprise_api_service_client = api_client()

        mocked_jwt_builder.assert_called_once_with(enterprise_service_user)
        # pylint: disable=protected-access
        self.assertEqual(enterprise_api_service_client.client._store['session'].auth.token, 'test-token')

    def _assert_api_client_with_user(self, api_client, mocked_jwt_builder):
        """
        Verify that the provided api client uses the expected user to generate
        JWT token for auth.
        """
        mocked_jwt_builder.return_value.build_token.return_value = 'test-token'
        dummy_enterprise_user = UserFactory.create(
            username='dummy-enterprise-user',
            email='dummy-enterprise-user@example.com',
            password='password123',
        )
        enterprise_api_service_client = api_client(dummy_enterprise_user)

        mocked_jwt_builder.assert_called_once_with(dummy_enterprise_user)
        # pylint: disable=protected-access
        self.assertEqual(enterprise_api_service_client.client._store['session'].auth.token, 'test-token')

    def _assert_get_enterprise_customer(self, api_client):
        """
        DRY method to verify caching for get enterprise customer method.
        """
        dummy_enterprise_api_data = {'name': 'dummy-enterprise-customer', 'uuid': 'enterprise-uuid'}
        cache_key = get_cache_key(
            resource='enterprise-customer',
            username=settings.ENTERPRISE_SERVICE_WORKER_USERNAME,
        )
        self.mock_get_enterprise_customer('enterprise-uuid', dummy_enterprise_api_data, 200)
        self._assert_get_enterprise_customer_with_cache(api_client, dummy_enterprise_api_data, cache_key)

    def _assert_get_enterprise_customer_with_cache(self, api_client, enterprise_customer_data, cache_key):
        """
        DRY method to verify that get enterprise customer response is cached.
        """
        cached_enterprise_customer = cache.get(cache_key)
        self.assertIsNone(cached_enterprise_customer)

        enterprise_customer = api_client.get_enterprise_customer(enterprise_customer_data['uuid'])
        self.assertEqual(enterprise_customer_data, enterprise_customer)
        cached_enterprise_customer = cache.get(cache_key)
        self.assertEqual(cached_enterprise_customer, enterprise_customer)

    @httpretty.activate
    @mock.patch('openedx.features.enterprise_support.api.JwtBuilder')
    def test_enterprise_api_client_with_service_user(self, mock_jwt_builder):
        """
        Verify that enterprise API service client uses enterprise service user
        by default to authenticate and access enterprise API.
        """
        self._assert_api_service_client(EnterpriseApiServiceClient, mock_jwt_builder)

        # Now verify that enterprise customer data is cached properly for
        # the enterprise api client.
        enterprise_api_client = EnterpriseApiServiceClient()
        self._assert_get_enterprise_customer(enterprise_api_client)

    @httpretty.activate
    @mock.patch('openedx.features.enterprise_support.api.JwtBuilder')
    def test_enterprise_api_client_with_user(self, mock_jwt_builder):
        """
        Verify that enterprise API client uses the provided user to
        authenticate and access enterprise API.
        """
        self._assert_api_client_with_user(EnterpriseApiClient, mock_jwt_builder)

    @httpretty.activate
    @mock.patch('openedx.features.enterprise_support.api.JwtBuilder')
    def test_enterprise_consent_api_client_with_service_user(self, mock_jwt_builder):
        """
        Verify that enterprise API consent service client uses enterprise
        service user by default to authenticate and access enterprise API.
        """
        self._assert_api_service_client(ConsentApiServiceClient, mock_jwt_builder)

    @httpretty.activate
    @mock.patch('openedx.features.enterprise_support.api.JwtBuilder')
    def test_enterprise_consent_api_client_with_user(self, mock_jwt_builder):
        """
        Verify that enterprise API consent service client uses the provided
        user to authenticate and access enterprise API.
        """
        self._assert_api_client_with_user(ConsentApiClient, mock_jwt_builder)

    @httpretty.activate
    def test_consent_needed_for_course(self):
        user = mock.MagicMock(
            username='janedoe',
            is_authenticated=lambda: True,
        )
        request = mock.MagicMock(session={}, user=user)
        self.mock_enterprise_learner_api()
        self.mock_consent_missing(user.username, 'fake-course', 'cf246b88-d5f6-4908-a522-fc307e0b0c59')
        self.assertTrue(consent_needed_for_course(request, user, 'fake-course'))
        self.mock_consent_get(user.username, 'fake-course', 'cf246b88-d5f6-4908-a522-fc307e0b0c59')
        self.assertFalse(consent_needed_for_course(request, user, 'fake-course'))
        # Test that the result is cached when false (remove the HTTP mock so if the result
        # isn't cached, we'll fail spectacularly.)
        httpretty.reset()
        self.assertFalse(consent_needed_for_course(request, user, 'fake-course'))

    @httpretty.activate
    @mock.patch('openedx.features.enterprise_support.api.EnterpriseCustomer')
    @mock.patch('openedx.features.enterprise_support.api.get_partial_pipeline')
    @mock.patch('openedx.features.enterprise_support.api.Registry')
    def test_enterprise_customer_for_request(
            self,
            mock_registry,
            mock_partial,
            mock_enterprise_customer_model,
    ):
        def mock_get_enterprise_customer(**kwargs):
            uuid = kwargs.get('enterprise_customer_identity_provider__provider_id')
            if uuid:
                return mock.MagicMock(uuid=uuid, user=self.user)
            raise Exception

        dummy_request = mock.MagicMock(session={}, user=self.user)
        mock_enterprise_customer_model.objects.get.side_effect = mock_get_enterprise_customer
        mock_enterprise_customer_model.DoesNotExist = Exception
        mock_partial.return_value = True
        mock_registry.get_from_pipeline.return_value.provider_id = 'real-ent-uuid'

        # Verify that the method `enterprise_customer_for_request` returns
        # expected enterprise customer against the requesting user.
        self.mock_get_enterprise_customer('real-ent-uuid', {'real': 'enterprisecustomer'}, 200)
        enterprise_customer = enterprise_customer_for_request(dummy_request)
        self.assertEqual(enterprise_customer, {'real': 'enterprisecustomer'})

        httpretty.reset()

        # Verify that the method `enterprise_customer_for_request` returns no
        # enterprise customer if the enterprise customer API throws 404.
        self.mock_get_enterprise_customer('real-ent-uuid', {'detail': 'Not found.'}, 404)
        enterprise_customer = enterprise_customer_for_request(dummy_request)
        self.assertIsNone(enterprise_customer)

        httpretty.reset()

        # Verify that the method `enterprise_customer_for_request` returns
        # expected enterprise customer against the requesting user even if
        # the third-party auth pipeline has no `provider_id`.
        mock_registry.get_from_pipeline.return_value.provider_id = None
        self.mock_get_enterprise_customer('real-ent-uuid', {'real': 'enterprisecustomer'}, 200)
        enterprise_customer = enterprise_customer_for_request(
            mock.MagicMock(GET={'enterprise_customer': 'real-ent-uuid'}, user=self.user)
        )
        self.assertEqual(enterprise_customer, {'real': 'enterprisecustomer'})

        # Verify that the method `enterprise_customer_for_request` returns
        # expected enterprise customer against the requesting user even if
        # the third-party auth pipeline has no `provider_id` but there is
        # enterprise customer UUID in the cookie.
        enterprise_customer = enterprise_customer_for_request(
            mock.MagicMock(GET={}, COOKIES={settings.ENTERPRISE_CUSTOMER_COOKIE_NAME: 'real-ent-uuid'}, user=self.user)
        )
        self.assertEqual(enterprise_customer, {'real': 'enterprisecustomer'})

    def check_data_sharing_consent(self, consent_required=False, consent_url=None):
        """
        Used to test the data_sharing_consent_required view decorator.
        """

        # Test by wrapping a function that has the expected signature
        @data_sharing_consent_required
        def view_func(request, course_id, *args, **kwargs):
            """
            Return the function arguments, so they can be tested.
            """
            return ((request, course_id,) + args, kwargs)

        # Call the wrapped function
        args = (mock.MagicMock(), 'course-id', 'another arg', 'and another')
        kwargs = dict(a=1, b=2, c=3)
        response = view_func(*args, **kwargs)

        # If consent required, then the response should be a redirect to the consent URL, and the view function would
        # not be called.
        if consent_required:
            self.assertIsInstance(response, HttpResponseRedirect)
            self.assertEquals(response.url, consent_url)  # pylint: disable=no-member

        # Otherwise, the view function should have been called with the expected arguments.
        else:
            self.assertEqual(response, (args, kwargs))

    @mock.patch('openedx.features.enterprise_support.api.enterprise_enabled')
    @mock.patch('openedx.features.enterprise_support.api.consent_needed_for_course')
    def test_data_consent_required_enterprise_disabled(self,
                                                       mock_consent_necessary,
                                                       mock_enterprise_enabled):
        """
        Verify that the wrapped view is called directly when enterprise integration is disabled,
        without checking for course consent necessary.
        """
        mock_enterprise_enabled.return_value = False

        self.check_data_sharing_consent(consent_required=False)

        mock_enterprise_enabled.assert_called_once()
        mock_consent_necessary.assert_not_called()

    @mock.patch('openedx.features.enterprise_support.api.enterprise_enabled')
    @mock.patch('openedx.features.enterprise_support.api.consent_needed_for_course')
    def test_no_course_data_consent_required(self,
                                             mock_consent_necessary,
                                             mock_enterprise_enabled):

        """
        Verify that the wrapped view is called directly when enterprise integration is enabled,
        and no course consent is required.
        """
        mock_enterprise_enabled.return_value = True
        mock_consent_necessary.return_value = False

        self.check_data_sharing_consent(consent_required=False)

        mock_enterprise_enabled.assert_called_once()
        mock_consent_necessary.assert_called_once()

    @mock.patch('openedx.features.enterprise_support.api.enterprise_enabled')
    @mock.patch('openedx.features.enterprise_support.api.consent_needed_for_course')
    @mock.patch('openedx.features.enterprise_support.api.get_enterprise_consent_url')
    def test_data_consent_required(self, mock_get_consent_url, mock_consent_necessary, mock_enterprise_enabled):
        """
        Verify that the wrapped function returns a redirect to the consent URL when enterprise integration is enabled,
        and course consent is required.
        """
        mock_enterprise_enabled.return_value = True
        mock_consent_necessary.return_value = True
        consent_url = '/abc/def'
        mock_get_consent_url.return_value = consent_url

        self.check_data_sharing_consent(consent_required=True, consent_url=consent_url)

        mock_get_consent_url.assert_called_once()
        mock_enterprise_enabled.assert_called_once()
        mock_consent_necessary.assert_called_once()

    @mock.patch('openedx.features.enterprise_support.api.reverse')
    @mock.patch('openedx.features.enterprise_support.api.consent_needed_for_course')
    def test_get_enterprise_consent_url(self, needed_for_course_mock, reverse_mock):
        """
        Verify that get_enterprise_consent_url correctly builds URLs.
        """
        def fake_reverse(*args, **kwargs):
            if args[0] == 'grant_data_sharing_permissions':
                return '/enterprise/grant_data_sharing_permissions'
            return reverse(*args, **kwargs)

        reverse_mock.side_effect = fake_reverse
        needed_for_course_mock.return_value = True

        request_mock = mock.MagicMock(
            user=None,
            build_absolute_uri=lambda x: 'http://localhost:8000' + x  # Don't do it like this in prod. Ever.
        )

        course_id = 'course-v1:edX+DemoX+Demo_Course'
        return_to = 'info'

        expected_url = (
            '/enterprise/grant_data_sharing_permissions?course_id=course-v1%3AedX%2BDemoX%2BDemo_'
            'Course&failure_url=http%3A%2F%2Flocalhost%3A8000%2Fdashboard%3Fconsent_failed%3Dcou'
            'rse-v1%253AedX%252BDemoX%252BDemo_Course&next=http%3A%2F%2Flocalhost%3A8000%2Fcours'
            'es%2Fcourse-v1%3AedX%2BDemoX%2BDemo_Course%2Finfo'
        )
        actual_url = get_enterprise_consent_url(request_mock, course_id, return_to=return_to)
        self.assertEqual(actual_url, expected_url)

    @ddt.data(
        (False, {'real': 'enterprise', 'uuid': ''}, 'course', [], []),
        (True, {}, 'course', [], []),
        (True, {'real': 'enterprise'}, None, [], []),
        (True, {'name': 'GriffCo', 'uuid': ''}, 'real-course', [], []),
        (True, {'name': 'GriffCo', 'uuid': ''}, 'real-course', [MockEnrollment(course_id='other-id')], []),
        (
            True,
            {'name': 'GriffCo', 'uuid': 'real-uuid'},
            'real-course',
            [
                MockEnrollment(
                    course_id='real-course',
                    course_overview=mock.MagicMock(
                        display_name='My Cool Course'
                    )
                )
            ],
            [
                'If you have concerns about sharing your data, please contact your administrator at GriffCo.',
                'Enrollment in My Cool Course was not complete.'
            ]
        ),

    )
    @ddt.unpack
    @mock.patch('openedx.features.enterprise_support.api.ConsentApiClient')
    @mock.patch('openedx.features.enterprise_support.api.enterprise_customer_for_request')
    def test_get_dashboard_consent_notification(
            self,
            consent_return_value,
            enterprise_customer,
            course_id,
            enrollments,
            expected_substrings,
            ec_for_request,
            consent_client_class
    ):
        request = mock.MagicMock(
            GET={'consent_failed': course_id}
        )
        consent_client = consent_client_class.return_value
        consent_client.consent_required.return_value = consent_return_value

        ec_for_request.return_value = enterprise_customer

        user = mock.MagicMock()

        notification_string = get_dashboard_consent_notification(
            request, user, enrollments,
        )

        if expected_substrings:
            for substr in expected_substrings:
                self.assertIn(substr, notification_string)
        else:
            self.assertEqual(notification_string, '')
