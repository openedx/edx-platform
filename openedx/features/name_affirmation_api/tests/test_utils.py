""" Tests for Name Affirmation API utils """

from unittest import TestCase
from unittest.mock import patch

import ddt
from edx_django_utils.plugins import PluginError

from openedx.features.name_affirmation_api.utils import is_name_affirmation_installed, get_name_affirmation_service


@ddt.ddt
class TestNameAffirmationAPIUtils(TestCase):
    """ Tests for Name Affirmation API utils """

    @patch('openedx.features.name_affirmation_api.utils.PluginManager')
    def test_name_affirmation_installed(self, mock_manager):
        mock_manager.get_plugin.return_value = 'mock plugin'
        self.assertTrue(is_name_affirmation_installed())

    @patch('openedx.features.name_affirmation_api.utils.PluginManager')
    def test_name_affirmation_not_installed(self, mock_manager):
        mock_manager.side_effect = PluginError('No such plugin')
        with self.assertRaises(PluginError):
            self.assertFalse(is_name_affirmation_installed())

    @patch('edx_name_affirmation.services.NameAffirmationService')
    @ddt.data(True, False)
    def test_get_name_affirmation_service(self, name_affirmation_installed, mock_service):
        with patch('openedx.features.name_affirmation_api.utils.is_name_affirmation_installed',
                   return_value=name_affirmation_installed):
            name_affirmation_service = get_name_affirmation_service()
            if name_affirmation_installed:
                self.assertEqual(name_affirmation_service, mock_service())
            else:
                self.assertIsNone(name_affirmation_service)
