"""
Test the enterprise app helpers
"""
import unittest

from django.conf import settings
from django.http import HttpResponseRedirect
from django.test.utils import override_settings
import mock

from util.enterprise_helpers import (
    enterprise_enabled,
    insert_enterprise_pipeline_elements,
    data_sharing_consent_required,
    set_enterprise_branding_filter_param,
    get_enterprise_branding_filter_param,
    get_enterprise_customer_logo_url
)


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class TestEnterpriseHelpers(unittest.TestCase):
    """
    Test enterprise app helpers
    """

    @override_settings(ENABLE_ENTERPRISE_INTEGRATION=False)
    def test_utils_with_enterprise_disabled(self):
        """
        Test that disabling the enterprise integration flag causes
        the utilities to return the expected default values.
        """
        self.assertFalse(enterprise_enabled())
        self.assertEqual(insert_enterprise_pipeline_elements(None), None)

    @override_settings(ENABLE_ENTERPRISE_INTEGRATION=True)
    def test_utils_with_enterprise_enabled(self):
        """
        Test that enabling enterprise integration (which is currently on by default) causes the
        the utilities to return the expected values.
        """
        self.assertTrue(enterprise_enabled())
        pipeline = ['abc', 'social.pipeline.social_auth.load_extra_data', 'def']
        insert_enterprise_pipeline_elements(pipeline)
        self.assertEqual(pipeline, ['abc',
                                    'enterprise.tpa_pipeline.handle_enterprise_logistration',
                                    'social.pipeline.social_auth.load_extra_data',
                                    'def'])

    def test_set_enterprise_branding_filter_param(self):
        """
        Test that the enterprise customer branding parameters are setting correctly.
        """
        ec_uuid = '97b4a894-cea9-4103-8f9f-2c5c95a58ba3'
        provider_id = 'test-provider-idp'

        request = mock.MagicMock(session={}, GET={'ec_src': ec_uuid})
        set_enterprise_branding_filter_param(request, provider_id=None)
        self.assertEqual(get_enterprise_branding_filter_param(request), {'ec_uuid': ec_uuid})

        set_enterprise_branding_filter_param(request, provider_id=provider_id)
        self.assertEqual(get_enterprise_branding_filter_param(request), {'provider_id': provider_id})

    @override_settings(ENABLE_ENTERPRISE_INTEGRATION=True)
    def test_get_enterprise_customer_logo_url(self):
        """
        Test test_get_enterprise_customer_logo_url return the logo url as desired.
        """
        ec_uuid = '97b4a894-cea9-4103-8f9f-2c5c95a58ba3'
        provider_id = 'test-provider-idp'
        request = mock.MagicMock(session={}, GET={'ec_src': ec_uuid})
        branding_info = mock.Mock(
            logo=mock.Mock(
                url='/test/image.png'
            )
        )

        set_enterprise_branding_filter_param(request, provider_id=None)
        with mock.patch('enterprise.utils.get_enterprise_branding_info_by_ec_uuid', return_value=branding_info):
            logo_url = get_enterprise_customer_logo_url(request)
            self.assertEqual(logo_url, '/test/image.png')

        set_enterprise_branding_filter_param(request, provider_id)
        with mock.patch('enterprise.utils.get_enterprise_branding_info_by_provider_id', return_value=branding_info):
            logo_url = get_enterprise_customer_logo_url(request)
            self.assertEqual(logo_url, '/test/image.png')

    @override_settings(ENABLE_ENTERPRISE_INTEGRATION=False)
    def test_get_enterprise_customer_logo_url_return_none(self):
        """
        Test get_enterprise_customer_logo_url return 'None' when enterprise application is not installed.
        """
        request = mock.MagicMock(session={})
        branding_info = mock.Mock()

        set_enterprise_branding_filter_param(request, 'test-idp')
        with mock.patch('enterprise.utils.get_enterprise_branding_info_by_provider_id', return_value=branding_info):
            logo_url = get_enterprise_customer_logo_url(request)
            self.assertEqual(logo_url, None)

    @override_settings(ENABLE_ENTERPRISE_INTEGRATION=True)
    @mock.patch('util.enterprise_helpers.get_enterprise_branding_filter_param', mock.Mock(return_value=None))
    def test_get_enterprise_customer_logo_url_return_none_when_param_missing(self):
        """
        Test get_enterprise_customer_logo_url return 'None' when filter parameters are missing.
        """
        request = mock.MagicMock(session={})
        branding_info = mock.Mock()

        set_enterprise_branding_filter_param(request, provider_id=None)
        with mock.patch('enterprise.utils.get_enterprise_branding_info_by_provider_id', return_value=branding_info):
            logo_url = get_enterprise_customer_logo_url(request)
            self.assertEqual(logo_url, None)

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

    @mock.patch('util.enterprise_helpers.enterprise_enabled')
    @mock.patch('util.enterprise_helpers.consent_necessary_for_course')
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

    @mock.patch('util.enterprise_helpers.enterprise_enabled')
    @mock.patch('util.enterprise_helpers.consent_necessary_for_course')
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

    @mock.patch('util.enterprise_helpers.enterprise_enabled')
    @mock.patch('util.enterprise_helpers.consent_necessary_for_course')
    @mock.patch('util.enterprise_helpers.get_enterprise_consent_url')
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
