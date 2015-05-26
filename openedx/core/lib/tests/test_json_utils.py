"""
Tests for json_utils.py
"""
import json
from unittest import TestCase

from openedx.core.lib.json_utils import EscapedEdxJSONEncoder


class TestEscapedEdxJSONEncoder(TestCase):
    """Test the EscapedEdxJSONEncoder class."""
    def test_escapes_forward_slashes(self):
        """Verify that we escape forward slashes with backslashes."""
        malicious_json = {'</script><script>alert("hello, ");</script>': '</script><script>alert("world!");</script>'}
        self.assertNotIn(
            '</script>',
            json.dumps(malicious_json, cls=EscapedEdxJSONEncoder)
        )
