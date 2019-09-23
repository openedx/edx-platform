# -*- coding: utf-8 -*-
"""
Tests for Blockstore-based Content Libraries
"""
from __future__ import absolute_import, division, print_function, unicode_literals
import unittest
from uuid import UUID

from django.conf import settings
from organizations.models import Organization
from rest_framework.test import APITestCase

from student.tests.factories import UserFactory
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

URL_BLOCK_RENDER_VIEW = '/api/xblock/v2/xblocks/{block_key}/view/{view_name}/'
URL_BLOCK_GET_HANDLER_URL = '/api/xblock/v2/xblocks/{block_key}/handler_url/{handler_name}/'


@unittest.skipUnless(settings.RUN_BLOCKSTORE_TESTS, "Requires a running Blockstore server")
@unittest.skipUnless(settings.ROOT_URLCONF == "cms.urls", "Content Libraries REST API is only available in Studio")
class ContentLibrariesTest(APITestCase):
    """
    Test for Blockstore-based Content Libraries

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
        super(ContentLibrariesTest, cls).setUpClass()
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
        super(ContentLibrariesTest, self).setUp()
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

    # General Content Library tests

    def test_library_crud(self):
        """
        Test Create, Read, Update, and Delete of a Content Library
        """
        # Create:
        lib = self._create_library(slug="lib-crud", title="A Test Library", description="Just Testing")
        expected_data = {
            "id": "lib:CL-TEST:lib-crud",
            "org": "CL-TEST",
            "slug": "lib-crud",
            "title": "A Test Library",
            "description": "Just Testing",
            "version": 0,
            "has_unpublished_changes": False,
            "has_unpublished_deletes": False,
        }
        self.assertDictContainsSubset(expected_data, lib)
        # Check that bundle_uuid looks like a valid UUID
        UUID(lib["bundle_uuid"])  # will raise an exception if not valid

        # Read:
        lib2 = self._get_library(lib["id"])
        self.assertDictContainsSubset(expected_data, lib2)

        # Update:
        lib3 = self._update_library(lib["id"], title="New Title")
        expected_data["title"] = "New Title"
        self.assertDictContainsSubset(expected_data, lib3)

        # Delete:
        self._delete_library(lib["id"])
        # And confirm it is deleted:
        self._get_library(lib["id"], expect_response=404)
        self._delete_library(lib["id"], expect_response=404)

    def test_library_validation(self):
        """
        You can't create a library with the same slug as an existing library,
        or an invalid slug.
        """
        self._create_library(slug="some-slug", title="Existing Library")
        self._create_library(slug="some-slug", title="Duplicate Library", expect_response=400)

        self._create_library(slug="Invalid Slug!", title="Library with Bad Slug", expect_response=400)

    # General Content Library XBlock tests:

    def test_library_blocks(self):
        """
        Test the happy path of creating and working with XBlocks in a content
        library.
        """
        lib = self._create_library(slug="testlib1", title="A Test Library", description="Testing XBlocks")
        lib_id = lib["id"]
        self.assertEqual(lib["has_unpublished_changes"], False)

        # A library starts out empty:
        self.assertEqual(self._get_library_blocks(lib_id), [])

        # Add a 'problem' XBlock to the library:
        block_data = self._add_block_to_library(lib_id, "problem", "problem1")
        self.assertDictContainsSubset({
            "id": "lb:CL-TEST:testlib1:problem:problem1",
            "display_name": "Blank Advanced Problem",
            "block_type": "problem",
            "has_unpublished_changes": True,
        }, block_data)
        block_id = block_data["id"]
        # Confirm that the result contains a definition key, but don't check its value,
        # which for the purposes of these tests is an implementation detail.
        self.assertIn("def_key", block_data)

        # now the library should contain one block and have unpublished changes:
        self.assertEqual(self._get_library_blocks(lib_id), [block_data])
        self.assertEqual(self._get_library(lib_id)["has_unpublished_changes"], True)

        # Publish the changes:
        self._commit_library_changes(lib_id)
        self.assertEqual(self._get_library(lib_id)["has_unpublished_changes"], False)
        # And now the block information should also show that block has no unpublished changes:
        block_data["has_unpublished_changes"] = False
        self.assertDictContainsSubset(block_data, self._get_library_block(block_id))
        self.assertEqual(self._get_library_blocks(lib_id), [block_data])

        # Now update the block's OLX:
        orig_olx = self._get_library_block_olx(block_id)
        self.assertIn("<problem", orig_olx)
        new_olx = """
        <problem display_name="New Multi Choice Question" max_attempts="5">
            <multiplechoiceresponse>
                <p>This is a normal capa problem. It has "maximum attempts" set to **5**.</p>
                <label>Blockstore is designed to store.</label>
                <choicegroup type="MultipleChoice">
                    <choice correct="false">XBlock metadata only</choice>
                    <choice correct="true">XBlock data/metadata and associated static asset files</choice>
                    <choice correct="false">Static asset files for XBlocks and courseware</choice>
                    <choice correct="false">XModule metadata only</choice>
                </choicegroup>
            </multiplechoiceresponse>
        </problem>
        """.strip()
        self._set_library_block_olx(block_id, new_olx)
        # now reading it back, we should get that exact OLX (no change to whitespace etc.):
        self.assertEqual(self._get_library_block_olx(block_id), new_olx)
        # And the display name and "unpublished changes" status of the block should be updated:
        self.assertDictContainsSubset({
            "display_name": "New Multi Choice Question",
            "has_unpublished_changes": True,
        }, self._get_library_block(block_id))

        # Now view the XBlock's student_view (including draft changes):
        fragment = self._render_block_view(block_id, "student_view")
        self.assertIn("resources", fragment)
        self.assertIn("Blockstore is designed to store.", fragment["content"])

        # Also call a handler to make sure that's working:
        handler_url = self._get_block_handler_url(block_id, "xmodule_handler") + "problem_get"
        problem_get_response = self.client.get(handler_url)
        self.assertEqual(problem_get_response.status_code, 200)
        self.assertIn("You have used 0 of 5 attempts", problem_get_response.content)

        # Now delete the block:
        self.assertEqual(self._get_library(lib_id)["has_unpublished_deletes"], False)
        self._delete_library_block(block_id)
        # Confirm it's deleted:
        self._render_block_view(block_id, "student_view", expect_response=404)
        self._get_library_block(block_id, expect_response=404)
        self.assertEqual(self._get_library(lib_id)["has_unpublished_deletes"], True)

        # Now revert all the changes back until the last publish:
        self._revert_library_changes(lib_id)
        self.assertEqual(self._get_library(lib_id)["has_unpublished_deletes"], False)
        self.assertEqual(self._get_library_block_olx(block_id), orig_olx)

        # fin

    def test_library_blocks_with_hierarchy(self):
        """
        Test library blocks with children
        """
        lib = self._create_library(slug="hierarchy_test_lib", title="A Test Library")
        lib_id = lib["id"]

        # Add a 'unit' XBlock to the library:
        unit_block = self._add_block_to_library(lib_id, "unit", "unit1")
        # Add an HTML child block:
        child1 = self._add_block_to_library(lib_id, "html", "html1", parent_block=unit_block["id"])
        self._set_library_block_olx(child1["id"], "<html>Hello world</html>")
        # Add a problem child block:
        child2 = self._add_block_to_library(lib_id, "problem", "problem1", parent_block=unit_block["id"])
        self._set_library_block_olx(child2["id"], """
            <problem><multiplechoiceresponse>
                    <p>What is an even number?</p>
                    <choicegroup type="MultipleChoice">
                        <choice correct="false">3</choice>
                        <choice correct="true">2</choice>
                    </choicegroup>
            </multiplechoiceresponse></problem>
        """)

        # Check the resulting OLX of the unit:
        self.assertEqual(self._get_library_block_olx(unit_block["id"]), (
            '<unit xblock-family="xblock.v1">\n'
            '  <xblock-include definition="html/html1"/>\n'
            '  <xblock-include definition="problem/problem1"/>\n'
            '</unit>\n'
        ))

        # The unit can see and render its children:
        fragment = self._render_block_view(unit_block["id"], "student_view")
        self.assertIn("Hello world", fragment["content"])
        self.assertIn("What is an even number?", fragment["content"])

        # We cannot add a duplicate ID to the library, either at the top level or as a child:
        self._add_block_to_library(lib_id, "problem", "problem1", expect_response=400)
        self._add_block_to_library(lib_id, "problem", "problem1", parent_block=unit_block["id"], expect_response=400)
