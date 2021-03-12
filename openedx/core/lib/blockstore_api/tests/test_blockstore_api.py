# -*- coding: utf-8 -*-
"""
Tests for xblock_utils.py
"""

import unittest
from uuid import UUID

from django.conf import settings
from openedx.core.lib import blockstore_api as api

# A fake UUID that won't represent any real bundle/draft/collection:
BAD_UUID = UUID('12345678-0000-0000-0000-000000000000')


@unittest.skipUnless(settings.RUN_BLOCKSTORE_TESTS, "Requires a running Blockstore server")
class BlockstoreApiClientTest(unittest.TestCase):
    """
    Test for the Blockstore API Client.

    The goal of these tests is not to test that Blockstore works correctly, but
    that the API client can interact with it and all the API client methods
    work.
    """

    # Collections

    def test_nonexistent_collection(self):
        """ Request a collection that doesn't exist -> CollectionNotFound """
        with self.assertRaises(api.CollectionNotFound):
            api.get_collection(BAD_UUID)

    def test_collection_crud(self):
        """ Create, Fetch, Update, and Delete a Collection """
        title = "Fire 🔥 Collection"
        # Create:
        coll = api.create_collection(title)
        self.assertEqual(coll.title, title)
        self.assertIsInstance(coll.uuid, UUID)
        # Fetch:
        coll2 = api.get_collection(coll.uuid)
        self.assertEqual(coll, coll2)
        # Update:
        new_title = "Air 🌀 Collection"
        coll3 = api.update_collection(coll.uuid, title=new_title)
        self.assertEqual(coll3.title, new_title)
        coll4 = api.get_collection(coll.uuid)
        self.assertEqual(coll4.title, new_title)
        # Delete:
        api.delete_collection(coll.uuid)
        with self.assertRaises(api.CollectionNotFound):
            api.get_collection(coll.uuid)

    # Bundles

    def test_nonexistent_bundle(self):
        """ Request a bundle that doesn't exist -> BundleNotFound """
        with self.assertRaises(api.BundleNotFound):
            api.get_bundle(BAD_UUID)

    def test_bundle_crud(self):
        """ Create, Fetch, Update, and Delete a Bundle """
        coll = api.create_collection("Test Collection")
        args = {
            "title": "Water 💧 Bundle",
            "slug": "h2o",
            "description": "Sploosh",
        }
        # Create:
        bundle = api.create_bundle(coll.uuid, **args)
        for attr, value in args.items():
            self.assertEqual(getattr(bundle, attr), value)
        self.assertIsInstance(bundle.uuid, UUID)
        # Fetch:
        bundle2 = api.get_bundle(bundle.uuid)
        self.assertEqual(bundle, bundle2)
        # Update:
        new_description = "Water Nation Bending Lessons"
        bundle3 = api.update_bundle(bundle.uuid, description=new_description)
        self.assertEqual(bundle3.description, new_description)
        bundle4 = api.get_bundle(bundle.uuid)
        self.assertEqual(bundle4.description, new_description)
        # Delete:
        api.delete_bundle(bundle.uuid)
        with self.assertRaises(api.BundleNotFound):
            api.get_bundle(bundle.uuid)

    # Drafts, files, and reading/writing file contents:

    def test_nonexistent_draft(self):
        """ Request a draft that doesn't exist -> DraftNotFound """
        with self.assertRaises(api.DraftNotFound):
            api.get_draft(BAD_UUID)

    def test_drafts_and_files(self):
        """
        Test creating, reading, writing, committing, and reverting drafts and
        files.
        """
        coll = api.create_collection("Test Collection")
        bundle = api.create_bundle(coll.uuid, title="Earth 🗿 Bundle", slug="earth", description="another test bundle")
        # Create a draft
        draft = api.get_or_create_bundle_draft(bundle.uuid, draft_name="test-draft")
        self.assertEqual(draft.bundle_uuid, bundle.uuid)
        self.assertEqual(draft.name, "test-draft")
        self.assertGreaterEqual(draft.updated_at.year, 2019)
        # And retrieve it again:
        draft2 = api.get_or_create_bundle_draft(bundle.uuid, draft_name="test-draft")
        self.assertEqual(draft, draft2)
        # Also test retrieving using get_draft
        draft3 = api.get_draft(draft.uuid)
        self.assertEqual(draft, draft3)

        # Write a file into the bundle:
        api.write_draft_file(draft.uuid, "test.txt", b"initial version")
        # Now the file should be visible in the draft:
        draft_contents = api.get_bundle_file_data(bundle.uuid, "test.txt", use_draft=draft.name)
        self.assertEqual(draft_contents, b"initial version")
        api.commit_draft(draft.uuid)

        # Write a new version into the draft:
        api.write_draft_file(draft.uuid, "test.txt", b"modified version")
        published_contents = api.get_bundle_file_data(bundle.uuid, "test.txt")
        self.assertEqual(published_contents, b"initial version")
        draft_contents2 = api.get_bundle_file_data(bundle.uuid, "test.txt", use_draft=draft.name)
        self.assertEqual(draft_contents2, b"modified version")
        # Now delete the draft:
        api.delete_draft(draft.uuid)
        draft_contents3 = api.get_bundle_file_data(bundle.uuid, "test.txt", use_draft=draft.name)
        # Confirm the file is now reset:
        self.assertEqual(draft_contents3, b"initial version")

        # Finaly, test the get_bundle_file* methods:
        file_info1 = api.get_bundle_file_metadata(bundle.uuid, "test.txt")
        self.assertEqual(file_info1.path, "test.txt")
        self.assertEqual(file_info1.size, len(b"initial version"))
        self.assertEqual(file_info1.hash_digest, "a45a5c6716276a66c4005534a51453ab16ea63c4")

        self.assertEqual(list(api.get_bundle_files(bundle.uuid)), [file_info1])
        self.assertEqual(api.get_bundle_files_dict(bundle.uuid), {
            "test.txt": file_info1,
        })

    # Links

    def test_links(self):
        """
        Test operations involving bundle links.
        """
        coll = api.create_collection("Test Collection")
        # Create two library bundles and a course bundle:
        lib1_bundle = api.create_bundle(coll.uuid, title="Library 1", slug="lib1")
        lib1_draft = api.get_or_create_bundle_draft(lib1_bundle.uuid, draft_name="test-draft")
        lib2_bundle = api.create_bundle(coll.uuid, title="Library 1", slug="lib2")
        lib2_draft = api.get_or_create_bundle_draft(lib2_bundle.uuid, draft_name="other-draft")
        course_bundle = api.create_bundle(coll.uuid, title="Library 1", slug="course")
        course_draft = api.get_or_create_bundle_draft(course_bundle.uuid, draft_name="test-draft")

        # To create links, we need valid BundleVersions, which requires having committed at least one change:
        api.write_draft_file(lib1_draft.uuid, "lib1-data.txt", "hello world")
        api.commit_draft(lib1_draft.uuid)  # Creates version 1
        api.write_draft_file(lib2_draft.uuid, "lib2-data.txt", "hello world")
        api.commit_draft(lib2_draft.uuid)  # Creates version 1

        # Lib2 has no links:
        self.assertFalse(api.get_bundle_links(lib2_bundle.uuid))

        # Create a link from lib2 to lib1
        link1_name = "lib2_to_lib1"
        api.set_draft_link(lib2_draft.uuid, link1_name, lib1_bundle.uuid, version=1)
        # Now confirm the link exists in the draft:
        lib2_draft_links = api.get_bundle_links(lib2_bundle.uuid, use_draft=lib2_draft.name)
        self.assertIn(link1_name, lib2_draft_links)
        self.assertEqual(lib2_draft_links[link1_name].direct.bundle_uuid, lib1_bundle.uuid)
        self.assertEqual(lib2_draft_links[link1_name].direct.version, 1)
        # Now commit the change to lib2:
        api.commit_draft(lib2_draft.uuid)  # Creates version 2

        # Now create a link from course to lib2
        link2_name = "course_to_lib2"
        api.set_draft_link(course_draft.uuid, link2_name, lib2_bundle.uuid, version=2)
        api.commit_draft(course_draft.uuid)

        # And confirm the link exists in the resulting bundle version:
        course_links = api.get_bundle_links(course_bundle.uuid)
        self.assertIn(link2_name, course_links)
        self.assertEqual(course_links[link2_name].direct.bundle_uuid, lib2_bundle.uuid)
        self.assertEqual(course_links[link2_name].direct.version, 2)
        # And since the links go course->lib2->lib1, course has an indirect link to lib1:
        self.assertEqual(course_links[link2_name].indirect[0].bundle_uuid, lib1_bundle.uuid)
        self.assertEqual(course_links[link2_name].indirect[0].version, 1)

        # Finally, test deleting a link from course's draft:
        api.set_draft_link(course_draft.uuid, link2_name, None, None)
        self.assertFalse(api.get_bundle_links(course_bundle.uuid, use_draft=course_draft.name))
