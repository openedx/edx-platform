"""
Tests for Content-Security-Policy middleware.
"""

from unittest import TestCase
from unittest.mock import MagicMock, patch

import ddt

from openedx.core.lib.csp_options.middleware import EdxCSPOptionsMiddleware


@ddt.ddt
class TestCSPOptionsMiddleware(TestCase):
    """Test the CSP middleware."""

    def test_on_no_override(self, settings, validate_header):
        """
        no override test
        """

    def test_on_override(self, settings, validate_header):
        """
        override test
        """

    def test_csp_defaults_to_none(self):
        """
        default test
        """
