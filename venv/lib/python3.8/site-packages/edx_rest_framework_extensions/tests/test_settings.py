""" Tests for settings. """
import warnings
from unittest import mock

from django.conf import settings
from django.test import TestCase, override_settings

from edx_rest_framework_extensions.settings import get_jwt_issuers, get_setting


class SettingsTests(TestCase):
    """ Tests for settings retrieval. """

    @override_settings(EDX_DRF_EXTENSIONS={})
    def test_get_setting_with_missing_key(self):
        """ Verify the function raises KeyError if the setting is not defined. """
        self.assertRaises(KeyError, get_setting, 'not_defined')

    def test_get_setting(self):
        """ Verify the function returns the value of the specified setting from the EDX_DRF_EXTENSIONS dict. """

        _settings = {
            'some-setting': 'some-value',
            'another-one': False
        }

        with override_settings(EDX_DRF_EXTENSIONS=_settings):
            for key, value in _settings.items():
                self.assertEqual(get_setting(key), value)

    def test_get_current_jwt_issuers(self):
        """
        Verify the get_jwt_issuers operation returns the current issuer information when configured
        """
        self.assertEqual(get_jwt_issuers(), settings.JWT_AUTH['JWT_ISSUERS'])

    def test_get_deprecated_jwt_issuers(self):
        """
        Verify the get_jwt_issuers operation returns the deprecated issuer information when current
        issuers are not configured for the system.
        """
        _deprecated = [
            {
                'ISSUER': settings.JWT_AUTH['JWT_ISSUER'],
                'SECRET_KEY': settings.JWT_AUTH['JWT_SECRET_KEY'],
                'AUDIENCE': settings.JWT_AUTH['JWT_AUDIENCE'],
            }
        ]

        mock_call = 'edx_rest_framework_extensions.settings._get_current_jwt_issuers'
        with mock.patch(mock_call, mock.Mock(return_value=None)):
            with warnings.catch_warnings(record=True) as warning_list:
                warnings.simplefilter("default")
                self.assertEqual(get_jwt_issuers(), _deprecated)
                self.assertEqual(len(warning_list), 1)
                self.assertTrue(issubclass(warning_list[-1].category, DeprecationWarning))
                msg = "'JWT_ISSUERS' list not defined, checking for deprecated settings."
                self.assertIn(msg, str(warning_list[-1].message))
