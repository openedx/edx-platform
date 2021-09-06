# -*- coding: utf-8 -*-
"""
Tests for Blockstore-based Content Libraries
"""
import unittest
from uuid import UUID

from django.contrib.auth.models import Group

from openedx.core.djangoapps.content_libraries.tests.base import ContentLibrariesRestApiTest
from student.tests.factories import UserFactory


class ContentLibrariesTest(ContentLibrariesRestApiTest):
    """
    General tests for Blockstore-based Content Libraries

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
        self.assertDictContainsEntries(lib, expected_data)
        # Check that bundle_uuid looks like a valid UUID
        UUID(lib["bundle_uuid"])  # will raise an exception if not valid

        # Read:
        lib2 = self._get_library(lib["id"])
        self.assertDictContainsEntries(lib2, expected_data)

        # Update:
        lib3 = self._update_library(lib["id"], title="New Title")
        expected_data["title"] = "New Title"
        self.assertDictContainsEntries(lib3, expected_data)

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
        self.assertDictContainsEntries(block_data, {
            "id": "lb:CL-TEST:testlib1:problem:problem1",
            "display_name": "Blank Advanced Problem",
            "block_type": "problem",
            "has_unpublished_changes": True,
        })
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
        self.assertDictContainsEntries(self._get_library_block(block_id), block_data)
        self.assertEqual(self._get_library_blocks(lib_id), [block_data])

        # Now update the block's OLX:
        orig_olx = self._get_library_block_olx(block_id)
        self.assertIn("<problem", orig_olx)
        new_olx = """
        <problem display_name="New Multi Choice Question" max_attempts="5">
            <multiplechoiceresponse>
                <p>This is a normal capa problem with unicode 🔥. It has "maximum attempts" set to **5**.</p>
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
        self.assertDictContainsEntries(self._get_library_block(block_id), {
            "display_name": "New Multi Choice Question",
            "has_unpublished_changes": True,
        })

        # Now view the XBlock's student_view (including draft changes):
        fragment = self._render_block_view(block_id, "student_view")
        self.assertIn("resources", fragment)
        self.assertIn("Blockstore is designed to store.", fragment["content"])

        # Also call a handler to make sure that's working:
        handler_url = self._get_block_handler_url(block_id, "xmodule_handler") + "problem_get"
        problem_get_response = self.client.get(handler_url)
        self.assertEqual(problem_get_response.status_code, 200)
        self.assertIn("You have used 0 of 5 attempts", problem_get_response.content.decode('utf-8'))

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

    # Test that permissions are enforced for content libraries

    def test_library_permissions(self):  # pylint: disable=too-many-statements
        """
        Test that permissions are enforced for content libraries, and that
        permissions can be read and manipulated using the REST API (which in
        turn tests the python API).

        This is a single giant test case, because that optimizes for the fastest
        test run time, even though it can make debugging failures harder.
        """
        # Create a few users to use for all of these tests:
        admin = UserFactory.create(username="Admin", email="admin@example.com")
        author = UserFactory.create(username="Author", email="author@example.com")
        reader = UserFactory.create(username="Reader", email="reader@example.com")
        group = Group.objects.create(name="group1")
        author_group_member = UserFactory.create(username="GroupMember", email="groupmember@example.com")
        author_group_member.groups.add(group)
        random_user = UserFactory.create(username="Random", email="random@example.com")

        # Library CRUD #########################################################

        # Create a library, owned by "Admin"
        with self.as_user(admin):
            lib = self._create_library(slug="permtest", title="Permission Test Library", description="Testing")
            lib_id = lib["id"]
            # By default, "public learning" and public read access are disallowed.
            self.assertEqual(lib["allow_public_learning"], False)
            self.assertEqual(lib["allow_public_read"], False)

            # By default, the creator of a new library is the only admin
            data = self._get_library_team(lib_id)
            self.assertEqual(len(data), 1)
            self.assertDictContainsEntries(data[0], {"user_id": admin.pk, "group_name": None, "access_level": "admin"})

            # Add the other users to the content library:
            self._set_user_access_level(lib_id, author.pk, access_level="author")
            self._set_user_access_level(lib_id, reader.pk, access_level="read")
            self._set_group_access_level(lib_id, group.name, access_level="author")

            team_response = self._get_library_team(lib_id)
            self.assertEqual(len(team_response), 4)
            # The response should also always be sorted in a specific order (by username and group name):
            expected_response = [
                {"user_id": None, "group_name": "group1", "access_level": "author"},
                {"user_id": admin.pk, "group_name": None, "access_level": "admin"},
                {"user_id": author.pk, "group_name": None, "access_level": "author"},
                {"user_id": reader.pk, "group_name": None, "access_level": "read"},
            ]
            for entry, expected in zip(team_response, expected_response):
                self.assertDictContainsEntries(entry, expected)

        # A random user cannot get the library nor its team:
        with self.as_user(random_user):
            self._get_library(lib_id, expect_response=403)
            self._get_library_team(lib_id, expect_response=403)

        # But every authorized user can:
        for user in [admin, author, author_group_member]:
            with self.as_user(user):
                self._get_library(lib_id)
                data = self._get_library_team(lib_id)
                self.assertEqual(data, team_response)

        # A user with only read permission can get data about the library but not the team:
        with self.as_user(reader):
            self._get_library(lib_id)
            self._get_library_team(lib_id, expect_response=403)

        # Users without admin access cannot delete the library nor change its team:
        for user in [author, reader, author_group_member, random_user]:
            with self.as_user(user):
                self._delete_library(lib_id, expect_response=403)
                self._set_user_access_level(lib_id, author.pk, access_level="admin", expect_response=403)
                self._set_user_access_level(lib_id, admin.pk, access_level=None, expect_response=403)
                self._set_user_access_level(lib_id, random_user.pk, access_level="read", expect_response=403)

        # Users with author access (or higher) can edit the library's properties:
        with self.as_user(author):
            self._update_library(lib_id, description="Revised description")
        with self.as_user(author_group_member):
            self._update_library(lib_id, title="New Library Title")
        # But other users cannot:
        with self.as_user(reader):
            self._update_library(lib_id, description="Prohibited description", expect_response=403)
        with self.as_user(random_user):
            self._update_library(lib_id, title="I can't set this title", expect_response=403)
        # Verify the permitted changes were made:
        with self.as_user(admin):
            data = self._get_library(lib_id)
            self.assertEqual(data["description"], "Revised description")
            self.assertEqual(data["title"], "New Library Title")

        # Library XBlock editing ###############################################

        # users with read permission or less cannot add blocks:
        for user in [reader, random_user]:
            with self.as_user(user):
                self._add_block_to_library(lib_id, "problem", "problem1", expect_response=403)
        # But authors and admins can:
        with self.as_user(admin):
            self._add_block_to_library(lib_id, "problem", "problem1")
        with self.as_user(author):
            self._add_block_to_library(lib_id, "problem", "problem2")
        with self.as_user(author_group_member):
            block3_data = self._add_block_to_library(lib_id, "problem", "problem3")
            block3_key = block3_data["id"]

        # At this point, the library contains 3 draft problem XBlocks.

        # A random user cannot read OLX nor assets (this library has allow_public_read False):
        with self.as_user(random_user):
            self._get_library_block_olx(block3_key, expect_response=403)
            self._get_library_block_assets(block3_key, expect_response=403)
            self._get_library_block_asset(block3_key, file_name="whatever.png", expect_response=403)
        # But if we grant allow_public_read, then they can:
        with self.as_user(admin):
            self._update_library(lib_id, allow_public_read=True)
            self._set_library_block_asset(block3_key, "whatever.png", b"data")
        with self.as_user(random_user):
            self._get_library_block_olx(block3_key)
            self._get_library_block_assets(block3_key)
            self._get_library_block_asset(block3_key, file_name="whatever.png")

        # Users without authoring permission cannot edit nor delete XBlocks (this library has allow_public_read False):
        for user in [reader, random_user]:
            with self.as_user(user):
                self._set_library_block_olx(block3_key, "<problem/>", expect_response=403)
                self._set_library_block_asset(block3_key, "test.txt", b"data", expect_response=403)
                self._delete_library_block(block3_key, expect_response=403)
                self._commit_library_changes(lib_id, expect_response=403)
                self._revert_library_changes(lib_id, expect_response=403)

        # But users with author permission can:
        with self.as_user(author_group_member):
            olx = self._get_library_block_olx(block3_key)
            self._set_library_block_olx(block3_key, olx)
            self._get_library_block_assets(block3_key)
            self._set_library_block_asset(block3_key, "test.txt", b"data")
            self._get_library_block_asset(block3_key, file_name="test.txt")
            self._delete_library_block(block3_key)
            self._commit_library_changes(lib_id)
            self._revert_library_changes(lib_id)  # This is a no-op after the commit, but should still have 200 response

    def test_library_blocks_with_links(self):
        """
        Test that libraries can link to XBlocks in other content libraries
        """
        # Create a problem bank:
        bank_lib = self._create_library(slug="problem_bank", title="Problem Bank")
        bank_lib_id = bank_lib["id"]
        # Add problem1 to the problem bank:
        p1 = self._add_block_to_library(bank_lib_id, "problem", "problem1")
        self._set_library_block_olx(p1["id"], """
            <problem><multiplechoiceresponse>
                    <p>What is an even number?</p>
                    <choicegroup type="MultipleChoice">
                        <choice correct="false">3</choice>
                        <choice correct="true">2</choice>
                    </choicegroup>
            </multiplechoiceresponse></problem>
        """)
        # Commit the changes, creating version 1:
        self._commit_library_changes(bank_lib_id)
        # Now update problem 1 and create a new problem 2:
        self._set_library_block_olx(p1["id"], """
            <problem><multiplechoiceresponse>
                    <p>What is an odd number?</p>
                    <choicegroup type="MultipleChoice">
                        <choice correct="true">3</choice>
                        <choice correct="false">2</choice>
                    </choicegroup>
            </multiplechoiceresponse></problem>
        """)
        p2 = self._add_block_to_library(bank_lib_id, "problem", "problem2")
        self._set_library_block_olx(p2["id"], """
            <problem><multiplechoiceresponse>
                    <p>What holds this XBlock?</p>
                    <choicegroup type="MultipleChoice">
                        <choice correct="false">A course</choice>
                        <choice correct="true">A problem bank</choice>
                    </choicegroup>
            </multiplechoiceresponse></problem>
        """)
        # Commit the changes, creating version 2:
        self._commit_library_changes(bank_lib_id)
        # At this point, bank_lib contains two problems and has two versions.
        # In version 1, problem1 is "What is an event number", and in version 2 it's "What is an odd number".
        # Problem2 exists only in version 2 and asks "What holds this XBlock?"

        lib = self._create_library(slug="links_test_lib", title="Link Test Library")
        lib_id = lib["id"]
        # Link to the problem bank:
        self._link_to_library(lib_id, "problem_bank", bank_lib_id)
        self._link_to_library(lib_id, "problem_bank_v1", bank_lib_id, version=1)

        # Add a 'unit' XBlock to the library:
        unit_block = self._add_block_to_library(lib_id, "unit", "unit1")
        self._set_library_block_olx(unit_block["id"], """
            <unit>
                <!-- version 2 link to "What is an odd number?" -->
                <xblock-include source="problem_bank" definition="problem/problem1"/>
                <!-- version 1 link to "What is an even number?" -->
                <xblock-include source="problem_bank_v1" definition="problem/problem1" usage="p1v1" />
                <!-- link to "What holds this XBlock?" -->
                <xblock-include source="problem_bank" definition="problem/problem2"/>
            </unit>
        """)

        # The unit can see and render its children:
        fragment = self._render_block_view(unit_block["id"], "student_view")
        self.assertIn("What is an odd number?", fragment["content"])
        self.assertIn("What is an even number?", fragment["content"])
        self.assertIn("What holds this XBlock?", fragment["content"])

        # Also check the API for retrieving links:
        links_created = self._get_library_links(lib_id)
        links_created.sort(key=lambda link: link["id"])
        self.assertEqual(len(links_created), 2)

        self.assertEqual(links_created[0]["id"], "problem_bank")
        self.assertEqual(links_created[0]["bundle_uuid"], bank_lib["bundle_uuid"])
        self.assertEqual(links_created[0]["version"], 2)
        self.assertEqual(links_created[0]["latest_version"], 2)
        self.assertEqual(links_created[0]["opaque_key"], bank_lib_id)

        self.assertEqual(links_created[1]["id"], "problem_bank_v1")
        self.assertEqual(links_created[1]["bundle_uuid"], bank_lib["bundle_uuid"])
        self.assertEqual(links_created[1]["version"], 1)
        self.assertEqual(links_created[1]["latest_version"], 2)
        self.assertEqual(links_created[1]["opaque_key"], bank_lib_id)
