"""
Tests for LTI views.
"""

from django.test import TestCase

from .base import URL_LIB_LTI_JWKS
from .base import skip_unless_cms


@skip_unless_cms
class LtiToolJwksViewTest(TestCase):
    """
    Test JWKS view.
    """

    def test_when_no_keys_then_return_empty(self):
        """
        Given no LTI tool in the database.
        When JWKS requested.
        Then return empty
        """
        response = self.client.get(URL_LIB_LTI_JWKS)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, '{"keys": []}')
