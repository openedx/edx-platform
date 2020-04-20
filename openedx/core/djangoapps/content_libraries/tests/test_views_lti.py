"""
Tests for LTI views.
"""

from django.test import TestCase
from openedx.core.djangoapps.content_libraries.constants import PROBLEM

from .base import URL_LIB_LTI_JWKS
from .base import skip_unless_cms, ContentLibrariesRestApiTest


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


class LibraryBlockLtiUrlViewTest(ContentLibrariesRestApiTest):
    """
    Test generating LTI URL for a block in a library.
    """

    def test_lti_url_generation(self):
        """
        Test the LTI URL generated from the block ID.
        """

        library = self._create_library(
            slug="libgg", title="A Test Library", description="Testing library", library_type=PROBLEM,
        )

        block = self._add_block_to_library(library['id'], PROBLEM, PROBLEM)
        usage_key = str(block.usage_key)

        url = f'/api/libraries/v2/blocks/{usage_key}/lti/'
        expected_lti_url = f"/api/libraries/v2/lti/1.3/launch/?id={usage_key}"

        response = self._api("GET", url, None, expect_response=200)

        self.assertDictEqual(response, {"lti_url": expected_lti_url})

    def test_block_not_found(self):
        """
        Test the LTI URL cannot be generated as the block not found.
        """

        self._create_library(
            slug="libgg", title="A Test Library", description="Testing library", library_type=PROBLEM,
        )

        self._api("GET", '/api/libraries/v2/blocks/not-existing-key/lti/', None, expect_response=404)
