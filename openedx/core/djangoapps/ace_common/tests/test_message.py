"""
Tests for ace message module
"""


import ddt
from django.test import TestCase
from mock import patch

from openedx.core.djangoapps.ace_common.message import BaseMessageType


@ddt.ddt
class TestAbsoluteUrl(TestCase):

    @ddt.data(
        ('test@example.com', True),
        ('', False),
        (None, False),
    )
    @ddt.unpack
    def test_from_email_address_in_message(self, from_address, has_from_address):
        """
        Tests presence of from_address option in ace message
        """
        with patch("openedx.core.djangoapps.site_configuration.helpers.get_value", return_value=from_address):
            ace_message_type = BaseMessageType()
            self.assertEqual('from_address' in ace_message_type.options, has_from_address)
            if from_address:
                self.assertEqual(ace_message_type.options.get('from_address'), from_address)
