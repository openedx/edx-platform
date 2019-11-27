# -*- coding: utf-8 -*-
"""
Tests for Blockstore-based Content Libraries
"""
from __future__ import absolute_import, division, print_function, unicode_literals
import unittest

from django.conf import settings
from organizations.models import Organization
from rest_framework.test import APITestCase
import six

from student.tests.factories import UserFactory
from openedx.core.djangolib.testing.utils import skip_unless_cms
from openedx.core.lib import blockstore_api

# Define the URLs here - don't use reverse() because we want to detect
# backwards-incompatible changes like changed URLs.
URL_PREFIX = '/api/libraries/v2/'
URL_LIB_CREATE = URL_PREFIX
URL_LIB_DETAIL = URL_PREFIX + '{lib_key}/'  # Get data about a library, update or delete library
URL_LIB_BLOCK_TYPES = URL_LIB_DETAIL + 'block_types/'  # Get the list of XBlock types that can be added to this library
URL_LIB_COMMIT = URL_LIB_DETAIL + 'commit/'  # Commit (POST) or revert (DELETE) all pending changes to this library
URL_LIB_BLOCKS = URL_LIB_DETAIL + 'blocks/'  # Get the list of XBlocks in this library, or add a new one
URL_LIB_BLOCK = URL_PREFIX + 'blocks/{block_key}/'  # Get data about a block, or delete it
URL_LIB_BLOCK_OLX = URL_LIB_BLOCK + 'olx/'  # Get or set the OLX of the specified XBlock
URL_LIB_BLOCK_ASSETS = URL_LIB_BLOCK + 'assets/'  # List the static asset files of the specified XBlock
URL_LIB_BLOCK_ASSET_FILE = URL_LIB_BLOCK + 'assets/{file_name}'  # Get, delete, or upload a specific static asset file

URL_BLOCK_RENDER_VIEW = '/api/xblock/v2/xblocks/{block_key}/view/{view_name}/'
URL_BLOCK_GET_HANDLER_URL = '/api/xblock/v2/xblocks/{block_key}/handler_url/{handler_name}/'


# Decorator for tests that require blockstore
requires_blockstore = unittest.skipUnless(settings.RUN_BLOCKSTORE_TESTS, "Requires a running Blockstore server")


@requires_blockstore
@skip_unless_cms  # Content Libraries REST API is only available in Studio
class ContentLibrariesRestApiTest(APITestCase):
    """
    Base class for Blockstore-based Content Libraries test that use the REST API

    These tests use the REST API, which in turn relies on the Python API.
    Some tests may use the python API directly if necessary to provide
    coverage of any code paths not accessible via the REST API.

    In general, these tests should
    (1) Use public APIs only - don't directly create data using other methods,
        which results in a less realistic test and ties the test suite too
        closely to specific implementation details.
        (Exception: users can be provisioned using a user factory)
    (2) Assert that fields are present in responses, but don't assert that the
        entire response has some specific shape. That way, things like adding
        new fields to an API response, which are backwards compatible, won't
        break any tests, but backwards-incompatible API changes will.

    WARNING: every test should have a unique library slug, because even though
    the django/mysql database gets reset for each test case, the lookup between
    library slug and bundle UUID does not because it's assumed to be immutable
    and cached forever.
    """

    @classmethod
    def setUpClass(cls):
        super(ContentLibrariesRestApiTest, cls).setUpClass()
        cls.user = UserFactory.create(username="Bob", email="bob@example.com", password="edx")
        # Create a collection using Blockstore API directly only because there
        # is not yet any Studio REST API for doing so:
        cls.collection = blockstore_api.create_collection("Content Library Test Collection")
        # Create an organization
        cls.organization = Organization.objects.create(
            name="Content Libraries Tachyon Exploration & Survey Team",
            short_name="CL-TEST",
        )

    def setUp(self):
        super(ContentLibrariesRestApiTest, self).setUp()
        self.client.login(username=self.user.username, password="edx")

    # API helpers

    def _api(self, method, url, data, expect_response):
        """
        Call a REST API
        """
        response = getattr(self.client, method)(url, data, format="json")
        self.assertEqual(
            response.status_code, expect_response,
            "Unexpected response code {}:\n{}".format(response.status_code, getattr(response, 'data', '(no data)')),
        )
        return response.data

    def _create_library(self, slug, title, description="", expect_response=200):
        """ Create a library """
        return self._api('post', URL_LIB_CREATE, {
            "org": self.organization.short_name,
            "slug": slug,
            "title": title,
            "description": description,
            "collection_uuid": str(self.collection.uuid),
        }, expect_response)

    def _get_library(self, lib_key, expect_response=200):
        """ Get a library """
        return self._api('get', URL_LIB_DETAIL.format(lib_key=lib_key), None, expect_response)

    def _update_library(self, lib_key, **data):
        """ Update an existing library """
        return self._api('patch', URL_LIB_DETAIL.format(lib_key=lib_key), data=data, expect_response=200)

    def _delete_library(self, lib_key, expect_response=200):
        """ Delete an existing library """
        return self._api('delete', URL_LIB_DETAIL.format(lib_key=lib_key), None, expect_response)

    def _commit_library_changes(self, lib_key):
        """ Commit changes to an existing library """
        return self._api('post', URL_LIB_COMMIT.format(lib_key=lib_key), None, expect_response=200)

    def _revert_library_changes(self, lib_key):
        """ Revert pending changes to an existing library """
        return self._api('delete', URL_LIB_COMMIT.format(lib_key=lib_key), None, expect_response=200)

    def _get_library_blocks(self, lib_key):
        """ Get the list of XBlocks in the library """
        return self._api('get', URL_LIB_BLOCKS.format(lib_key=lib_key), None, expect_response=200)

    def _add_block_to_library(self, lib_key, block_type, slug, parent_block=None, expect_response=200):
        """ Add a new XBlock to the library """
        data = {"block_type": block_type, "definition_id": slug}
        if parent_block:
            data["parent_block"] = parent_block
        return self._api('post', URL_LIB_BLOCKS.format(lib_key=lib_key), data, expect_response)

    def _get_library_block(self, block_key, expect_response=200):
        """ Get a specific block in the library """
        return self._api('get', URL_LIB_BLOCK.format(block_key=block_key), None, expect_response)

    def _delete_library_block(self, block_key, expect_response=200):
        """ Delete a specific block from the library """
        self._api('delete', URL_LIB_BLOCK.format(block_key=block_key), None, expect_response)

    def _get_library_block_olx(self, block_key, expect_response=200):
        """ Get the OLX of a specific block in the library """
        result = self._api('get', URL_LIB_BLOCK_OLX.format(block_key=block_key), None, expect_response)
        if expect_response == 200:
            return result["olx"]
        return result

    def _set_library_block_olx(self, block_key, new_olx, expect_response=200):
        """ Overwrite the OLX of a specific block in the library """
        return self._api('post', URL_LIB_BLOCK_OLX.format(block_key=block_key), {"olx": new_olx}, expect_response)

    def _get_library_block_assets(self, block_key, expect_response=200):
        """ List the static asset files belonging to the specified XBlock """
        url = URL_LIB_BLOCK_ASSETS.format(block_key=block_key)
        result = self._api('get', url, None, expect_response)
        return result["files"] if expect_response == 200 else result

    def _get_library_block_asset(self, block_key, file_name, expect_response=200):
        """
        Get metadata about one static asset file belonging to the specified
        XBlock.
        """
        url = URL_LIB_BLOCK_ASSET_FILE.format(block_key=block_key, file_name=file_name)
        return self._api('get', url, None, expect_response)

    def _set_library_block_asset(self, block_key, file_name, content, expect_response=200):
        """
        Set/replace a static asset file belonging to the specified XBlock.

        content should be a binary string.
        """
        assert isinstance(content, six.binary_type)
        file_handle = six.BytesIO(content)
        url = URL_LIB_BLOCK_ASSET_FILE.format(block_key=block_key, file_name=file_name)
        response = self.client.put(url, data={"content": file_handle})
        self.assertEqual(
            response.status_code, expect_response,
            "Unexpected response code {}:\n{}".format(response.status_code, getattr(response, 'data', '(no data)')),
        )

    def _delete_library_block_asset(self, block_key, file_name, expect_response=200):
        """ Delete a static asset file. """
        url = URL_LIB_BLOCK_ASSET_FILE.format(block_key=block_key, file_name=file_name)
        return self._api('delete', url, None, expect_response)

    def _render_block_view(self, block_key, view_name, expect_response=200):
        """
        Render an XBlock's view in the active application's runtime.
        Note that this endpoint has different behavior in Studio (draft mode)
        vs. the LMS (published version only).
        """
        url = URL_BLOCK_RENDER_VIEW.format(block_key=block_key, view_name=view_name)
        return self._api('get', url, None, expect_response)

    def _get_block_handler_url(self, block_key, handler_name):
        """
        Get the URL to call a specific XBlock's handler.
        The URL itself encodes authentication information so can be called
        without session authentication or any other kind of authentication.
        """
        url = URL_BLOCK_GET_HANDLER_URL.format(block_key=block_key, handler_name=handler_name)
        return self._api('get', url, None, expect_response=200)["handler_url"]
