"""Tests of commerce utilities."""
from django.test import TestCase
from mock import patch

from commerce.utils import audit_log


class AuditLogTests(TestCase):
    """Tests of the commerce audit logging helper."""
    @patch('commerce.utils.log')
    def test_log_message(self, mock_log):
        """Verify that log messages are constructed correctly."""
        audit_log('foo', qux='quux', bar='baz')

        # Verify that the logged message contains comma-separated
        # key-value pairs ordered alphabetically by key.
        message = 'foo: bar="baz", qux="quux"'
        self.assertTrue(mock_log.info.called_with(message))
