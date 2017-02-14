"""
Test the enterprise app helpers
"""
import unittest

from django.conf import settings
import mock

from util.enterprise_helpers import (
    enterprise_enabled,
    insert_enterprise_pipeline_elements,
    set_enterprise_branding_filter_param,
    get_enterprise_branding_filter_param,
    get_enterprise_customer_logo_url
)


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class TestEnterpriseHelpers(unittest.TestCase):
    """
    Test enterprise app helpers
    """

    @mock.patch('util.enterprise_helpers.enterprise_enabled')
    def test_utils_with_enterprise_disabled(self, mock_enterprise_enabled):
        """
        Test that the enterprise app not being available causes
        the utilities to return the expected default values.
        """
        mock_enterprise_enabled.return_value = False
        self.assertEqual(insert_enterprise_pipeline_elements(None), None)

    def test_enterprise_enabled(self):
        """
        The test settings inherit from common, which have the enterprise
        app installed; therefore, it should appear installed here.
        """
        self.assertTrue(enterprise_enabled())

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

    @mock.patch('util.enterprise_helpers.enterprise_enabled', mock.Mock(return_value=True))
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

    @mock.patch('util.enterprise_helpers.enterprise_enabled', mock.Mock(return_value=False))
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

    @mock.patch('util.enterprise_helpers.enterprise_enabled', mock.Mock(return_value=True))
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
