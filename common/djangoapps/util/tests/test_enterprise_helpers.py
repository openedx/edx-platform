"""
Test the enterprise app helpers
"""
import unittest

from django.conf import settings
import mock

from util.enterprise_helpers import (
    enterprise_enabled,
    data_sharing_consent_requested,
    data_sharing_consent_required_at_login,
    data_sharing_consent_requirement_at_login,
    insert_enterprise_fields,
    insert_enterprise_pipeline_elements
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
        self.assertFalse(data_sharing_consent_requested(None))
        self.assertFalse(data_sharing_consent_required_at_login(None))
        self.assertEqual(data_sharing_consent_requirement_at_login(None), None)
        self.assertEqual(insert_enterprise_fields(None, None), None)
        self.assertEqual(insert_enterprise_pipeline_elements(None), None)

    def test_enterprise_enabled(self):
        """
        The test settings inherit from common, which have the enterprise
        app installed; therefore, it should appear installed here.
        """
        self.assertTrue(enterprise_enabled())

    @mock.patch('enterprise.tpa_pipeline.get_enterprise_customer_for_request')
    def test_data_sharing_consent_requested(self, mock_get_ec):
        """
        Test that we correctly check whether data sharing consent is requested.
        """
        request = mock.MagicMock(session={'partial_pipeline': 'thing'})
        mock_get_ec.return_value = mock.MagicMock(requests_data_sharing_consent=True)
        self.assertTrue(data_sharing_consent_requested(request))
        mock_get_ec.return_value = mock.MagicMock(requests_data_sharing_consent=False)
        self.assertFalse(data_sharing_consent_requested(request))
        mock_get_ec.return_value = None
        self.assertFalse(data_sharing_consent_requested(request))
        request = mock.MagicMock(session={})
        self.assertFalse(data_sharing_consent_requested(request))

    @mock.patch('enterprise.tpa_pipeline.get_enterprise_customer_for_request')
    def test_data_sharing_consent_required(self, mock_get_ec):
        """
        Test that we correctly check whether data sharing consent is required at login.
        """
        check_method = mock.MagicMock(return_value=True)
        request = mock.MagicMock(session={'partial_pipeline': 'thing'})
        mock_get_ec.return_value = mock.MagicMock(enforces_data_sharing_consent=check_method)
        self.assertTrue(data_sharing_consent_required_at_login(request))
        check_method.return_value = False
        mock_get_ec.return_value = mock.MagicMock(enforces_data_sharing_consent=check_method)
        self.assertFalse(data_sharing_consent_required_at_login(request))
        mock_get_ec.return_value = None
        self.assertFalse(data_sharing_consent_required_at_login(request))
        request = mock.MagicMock(session={})
        self.assertFalse(data_sharing_consent_required_at_login(request))

    @mock.patch('enterprise.tpa_pipeline.get_enterprise_customer_for_request')
    def test_data_sharing_consent_requirement(self, mock_get_ec):
        """
        Test that we get the correct requirement string for the current consent statae.
        """
        request = mock.MagicMock(session={'partial_pipeline': 'thing'})
        mock_ec = mock.MagicMock(
            enforces_data_sharing_consent=mock.MagicMock(return_value=True),
            requests_data_sharing_consent=True,
        )
        mock_get_ec.return_value = mock_ec
        self.assertEqual(data_sharing_consent_requirement_at_login(request), 'required')
        mock_ec.enforces_data_sharing_consent.return_value = False
        self.assertEqual(data_sharing_consent_requirement_at_login(request), 'optional')
        mock_ec.requests_data_sharing_consent = False
        self.assertEqual(data_sharing_consent_requirement_at_login(request), None)

    @mock.patch('util.enterprise_helpers.get_enterprise_customer_for_request')
    @mock.patch('enterprise.tpa_pipeline.get_enterprise_customer_for_request')
    @mock.patch('util.enterprise_helpers.configuration_helpers')
    def test_insert_enterprise_fields(self, mock_config_helpers, mock_get_ec, mock_get_ec2):
        """
        Test that the insertion of the enterprise fields is processed as expected.
        """
        request = mock.MagicMock(session={'partial_pipeline': 'thing'})
        mock_ec = mock.MagicMock(
            enforces_data_sharing_consent=mock.MagicMock(return_value=True),
            requests_data_sharing_consent=True,
        )
        # Name values in a MagicMock constructor don't fill a `name` attribute
        mock_ec.name = 'MassiveCorp'
        mock_get_ec.return_value = mock_ec
        mock_get_ec2.return_value = mock_ec
        mock_config_helpers.get_value.return_value = 'OpenEdX'
        form_desc = mock.MagicMock()
        form_desc.add_field.return_value = None
        expected_label = (
            "I agree to allow OpenEdX to share data about my enrollment, "
            "completion and performance in all OpenEdX courses and programs "
            "where my enrollment is sponsored by MassiveCorp."
        )
        expected_err_msg = (
            "To link your account with MassiveCorp, you are required to consent to data sharing."
        )
        insert_enterprise_fields(request, form_desc)
        mock_ec.enforces_data_sharing_consent.return_value = False
        insert_enterprise_fields(request, form_desc)
        calls = [
            mock.call(
                'data_sharing_consent',
                label=expected_label,
                field_type='checkbox',
                default=False,
                required=True,
                error_messages={'required': expected_err_msg}
            ),
            mock.call(
                'data_sharing_consent',
                label=expected_label,
                field_type='checkbox',
                default=False,
                required=False,
                error_messages={'required': expected_err_msg}
            )
        ]
        form_desc.add_field.assert_has_calls(calls)
        form_desc.add_field.reset_mock()
        mock_ec.requests_data_sharing_consent = False
        insert_enterprise_fields(request, form_desc)
        form_desc.add_field.assert_not_called()
