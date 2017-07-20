"""
Test the enterprise support APIs.
"""
import unittest

import mock
from django.conf import settings
from django.http import HttpResponseRedirect
from django.test.utils import override_settings

from openedx.features.enterprise_support.api import (
    data_sharing_consent_required,
    enterprise_customer_for_request,
    enterprise_enabled,
    get_dashboard_consent_notification,
    get_enterprise_consent_url,
)


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class TestEnterpriseApi(unittest.TestCase):
    """
    Test enterprise support APIs.
    """

    @override_settings(ENABLE_ENTERPRISE_INTEGRATION=True)
    @mock.patch('openedx.features.enterprise_support.api.EnterpriseCustomer')
    def test_enterprise_customer_for_request(self, ec_class_mock):
        """
        Test that the correct EnterpriseCustomer, if any, is returned.
        """
        def get_ec_mock(**kwargs):
            by_provider_id_kw = 'enterprise_customer_identity_provider__provider_id'
            provider_id = kwargs.get(by_provider_id_kw, '')
            uuid = kwargs.get('uuid', '')
            if uuid == 'real-uuid' or provider_id == 'real-provider-id':
                return 'this-is-actually-an-enterprise-customer'
            elif uuid == 'not-a-uuid':
                raise ValueError
            else:
                raise Exception

        ec_class_mock.DoesNotExist = Exception
        ec_class_mock.objects.get.side_effect = get_ec_mock

        request = mock.MagicMock()
        request.GET.get.return_value = 'real-uuid'
        self.assertEqual(enterprise_customer_for_request(request), 'this-is-actually-an-enterprise-customer')
        request.GET.get.return_value = 'not-a-uuid'
        self.assertEqual(enterprise_customer_for_request(request), None)
        request.GET.get.return_value = 'fake-uuid'
        self.assertEqual(enterprise_customer_for_request(request), None)
        request.GET.get.return_value = None
        self.assertEqual(
            enterprise_customer_for_request(request, tpa_hint='real-provider-id'),
            'this-is-actually-an-enterprise-customer'
        )
        self.assertEqual(enterprise_customer_for_request(request, tpa_hint='fake-provider-id'), None)
        self.assertEqual(enterprise_customer_for_request(request, tpa_hint=None), None)

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
    @mock.patch('openedx.features.enterprise_support.api.consent_necessary_for_course')
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
    @mock.patch('openedx.features.enterprise_support.api.consent_necessary_for_course')
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
    @mock.patch('openedx.features.enterprise_support.api.consent_necessary_for_course')
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

    @mock.patch('openedx.features.enterprise_support.api.consent_needed_for_course')
    def test_get_enterprise_consent_url(self, needed_for_course_mock):
        """
        Verify that get_enterprise_consent_url correctly builds URLs.
        """
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

    def test_get_dashboard_consent_notification_no_param(self):
        """
        Test that the output of the consent notification renderer meets expectations.
        """
        request = mock.MagicMock(
            GET={}
        )
        notification_string = get_dashboard_consent_notification(
            request, None, None
        )
        self.assertEqual(notification_string, '')

    def test_get_dashboard_consent_notification_no_enrollments(self):
        request = mock.MagicMock(
            GET={'consent_failed': 'course-v1:edX+DemoX+Demo_Course'}
        )
        enrollments = []
        user = mock.MagicMock(id=1)
        notification_string = get_dashboard_consent_notification(
            request, user, enrollments,
        )
        self.assertEqual(notification_string, '')

    def test_get_dashboard_consent_notification_no_matching_enrollments(self):
        request = mock.MagicMock(
            GET={'consent_failed': 'course-v1:edX+DemoX+Demo_Course'}
        )
        enrollments = [mock.MagicMock(course_id='other_course_id')]
        user = mock.MagicMock(id=1)
        notification_string = get_dashboard_consent_notification(
            request, user, enrollments,
        )
        self.assertEqual(notification_string, '')

    def test_get_dashboard_consent_notification_no_matching_ece(self):
        request = mock.MagicMock(
            GET={'consent_failed': 'course-v1:edX+DemoX+Demo_Course'}
        )
        enrollments = [mock.MagicMock(course_id='course-v1:edX+DemoX+Demo_Course')]
        user = mock.MagicMock(id=1)
        notification_string = get_dashboard_consent_notification(
            request, user, enrollments,
        )
        self.assertEqual(notification_string, '')

    @mock.patch('openedx.features.enterprise_support.api.EnterpriseCourseEnrollment')
    def test_get_dashboard_consent_notification_no_contact_info(self, ece_mock):
        mock_get_ece = ece_mock.objects.get
        ece_mock.DoesNotExist = Exception
        mock_ece = mock_get_ece.return_value
        mock_ece.enterprise_customer_user = mock.MagicMock(
            enterprise_customer=mock.MagicMock(
                contact_email=None
            )
        )
        mock_ec = mock_ece.enterprise_customer_user.enterprise_customer
        mock_ec.name = 'Veridian Dynamics'

        request = mock.MagicMock(
            GET={'consent_failed': 'course-v1:edX+DemoX+Demo_Course'}
        )
        enrollments = [
            mock.MagicMock(
                course_id='course-v1:edX+DemoX+Demo_Course',
                course_overview=mock.MagicMock(
                    display_name='edX Demo Course',
                )
            ),
        ]
        user = mock.MagicMock(id=1)
        notification_string = get_dashboard_consent_notification(
            request, user, enrollments,
        )
        expected_message = (
            'If you have concerns about sharing your data, please contact your '
            'administrator at Veridian Dynamics.'
        )
        self.assertIn(expected_message, notification_string)
        expected_header = 'Enrollment in edX Demo Course was not complete.'
        self.assertIn(expected_header, notification_string)

    @mock.patch('openedx.features.enterprise_support.api.EnterpriseCourseEnrollment')
    def test_get_dashboard_consent_notification_contact_info(self, ece_mock):
        mock_get_ece = ece_mock.objects.get
        ece_mock.DoesNotExist = Exception
        mock_ece = mock_get_ece.return_value
        mock_ece.enterprise_customer_user = mock.MagicMock(
            enterprise_customer=mock.MagicMock(
                contact_email='v.palmer@veridiandynamics.com'
            )
        )
        mock_ec = mock_ece.enterprise_customer_user.enterprise_customer
        mock_ec.name = 'Veridian Dynamics'

        request = mock.MagicMock(
            GET={'consent_failed': 'course-v1:edX+DemoX+Demo_Course'}
        )
        enrollments = [
            mock.MagicMock(
                course_id='course-v1:edX+DemoX+Demo_Course',
                course_overview=mock.MagicMock(
                    display_name='edX Demo Course',
                )
            ),
        ]
        user = mock.MagicMock(id=1)
        notification_string = get_dashboard_consent_notification(
            request, user, enrollments,
        )
        expected_message = (
            'If you have concerns about sharing your data, please contact your '
            'administrator at Veridian Dynamics at v.palmer@veridiandynamics.com.'
        )
        self.assertIn(expected_message, notification_string)
        expected_header = 'Enrollment in edX Demo Course was not complete.'
        self.assertIn(expected_header, notification_string)
