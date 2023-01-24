"""
Tests for Blockstore-based Content Libraries
"""
from uuid import UUID
from unittest.mock import patch

import ddt
from django.conf import settings
from django.contrib.auth.models import Group
from django.test.client import Client
from django.test.utils import override_settings
from organizations.models import Organization
from rest_framework.test import APITestCase

from openedx.core.djangoapps.content_libraries.libraries_index import LibraryBlockIndexer, ContentLibraryIndexer
from openedx.core.djangoapps.content_libraries.tests.base import (
    ContentLibrariesRestApiBlockstoreServiceTest,
    ContentLibrariesRestApiTest,
    elasticsearch_test,
    URL_BLOCK_METADATA_URL,
    URL_BLOCK_RENDER_VIEW,
    URL_BLOCK_GET_HANDLER_URL,
    URL_BLOCK_XBLOCK_HANDLER,
)
from openedx.core.djangoapps.content_libraries.constants import VIDEO, COMPLEX, PROBLEM, CC_4_BY, ALL_RIGHTS_RESERVED
from openedx.core.djangolib.blockstore_cache import cache
from openedx.core.lib import blockstore_api
from common.djangoapps.student.tests.factories import UserFactory


@ddt.ddt
class ContentLibrariesTestMixin:
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

    def setUp(self):
        super().setUp()
        if settings.ENABLE_ELASTICSEARCH_FOR_TESTS:
            ContentLibraryIndexer.remove_all_items()
            LibraryBlockIndexer.remove_all_items()

    def test_library_crud(self):
        """
        Test Create, Read, Update, and Delete of a Content Library
        """
        # Create:
        lib = self._create_library(
            slug="lib-crud", title="A Test Library", description="Just Testing", license_type=CC_4_BY,
        )
        expected_data = {
            "id": "lib:CL-TEST:lib-crud",
            "org": "CL-TEST",
            "slug": "lib-crud",
            "title": "A Test Library",
            "description": "Just Testing",
            "version": 0,
            "type": COMPLEX,
            "license": CC_4_BY,
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

    @ddt.data(VIDEO, PROBLEM, COMPLEX)
    def test_library_alternative_type(self, target_type):
        """
        Create a library with a specific type
        """
        lib = self._create_library(
            slug="some-slug", title="Video Library", description="Test Video Library", library_type=target_type,
        )
        expected_data = {
            "id": "lib:CL-TEST:some-slug",
            "org": "CL-TEST",
            "slug": "some-slug",
            "title": "Video Library",
            "type": target_type,
            "description": "Test Video Library",
            "version": 0,
            "has_unpublished_changes": False,
            "has_unpublished_deletes": False,
            "license": ALL_RIGHTS_RESERVED,
        }
        self.assertDictContainsEntries(lib, expected_data)

    # Need to use a different slug each time here. Seems to be a race condition on test cleanup that will break things
    # otherwise.
    @ddt.data(
        ('to-video-fail', COMPLEX, VIDEO, (("problem", "problemA"),), 400),
        ('to-video-empty', COMPLEX, VIDEO, tuple(), 200),
        ('to-problem', COMPLEX, PROBLEM, (("problem", "problemB"),), 200),
        ('to-problem-fail', COMPLEX, PROBLEM, (("video", "videoA"),), 400),
        ('to-problem-empty', COMPLEX, PROBLEM, tuple(), 200),
        ('to-complex-from-video', VIDEO, COMPLEX, (("video", "videoB"),), 200),
        ('to-complex-from-problem', PROBLEM, COMPLEX, (("problem", "problemC"),), 200),
        ('to-complex-from-problem-empty', PROBLEM, COMPLEX, tuple(), 200),
        ('to-problem-from-video-empty', PROBLEM, VIDEO, tuple(), 200),
    )
    @ddt.unpack
    def test_library_update_type_conversion(self, slug, start_type, target_type, xblock_specs, expect_response):
        """
        Test conversion of one library type to another. Restricts options based on type/block matching.
        """
        lib = self._create_library(
            slug=slug, title="A Test Library", description="Just Testing", library_type=start_type,
        )
        assert lib['type'] == start_type
        for block_type, block_slug in xblock_specs:
            self._add_block_to_library(lib['id'], block_type, block_slug)
        self._commit_library_changes(lib['id'])
        result = self._update_library(lib['id'], type=target_type, expect_response=expect_response)
        if expect_response == 200:
            assert result['type'] == target_type
            assert 'type' in result
        else:
            lib = self._get_library(lib['id'])
            assert lib['type'] == start_type

    def test_no_convert_on_unpublished(self):
        """
        Verify that you can't change a library's type, even if it would normally be valid,
        when there are unpublished changes. This is so that a reversion of blocks won't cause an inconsistency.
        """
        lib = self._create_library(
            slug='resolute', title="A complex library", description="Unconvertable", library_type=COMPLEX,
        )
        self._add_block_to_library(lib['id'], "video", 'vid-block')
        result = self._update_library(lib['id'], type=VIDEO, expect_response=400)
        assert 'type' in result

    def test_no_convert_on_pending_deletes(self):
        """
        Verify that you can't change a library's type, even if it would normally be valid,
        when there are unpublished changes. This is so that a reversion of blocks won't cause an inconsistency.
        """
        lib = self._create_library(
            slug='still-alive', title="A complex library", description="Unconvertable", library_type=COMPLEX,
        )
        block = self._add_block_to_library(lib['id'], "video", 'vid-block')
        self._commit_library_changes(lib['id'])
        self._delete_library_block(block['id'])
        result = self._update_library(lib['id'], type=VIDEO, expect_response=400)
        assert 'type' in result

    def test_library_validation(self):
        """
        You can't create a library with the same slug as an existing library,
        or an invalid slug.
        """
        assert 0 == len(blockstore_api.get_bundles(text_search='some-slug'))
        self._create_library(slug="some-slug", title="Existing Library")
        assert 1 == len(blockstore_api.get_bundles(text_search='some-slug'))

        # Try to create a library+bundle with a duplicate slug
        response = self._create_library(slug="some-slug", title="Duplicate Library", expect_response=400)
        assert response == {
            'slug': 'A library with that ID already exists.',
        }
        # The second bundle created with that slug is removed when the transaction rolls back.
        assert 1 == len(blockstore_api.get_bundles(text_search='some-slug'))

        response = self._create_library(slug="Invalid Slug!", title="Library with Bad Slug", expect_response=400)
        assert response == {
            'slug': ['Enter a valid “slug” consisting of Unicode letters, numbers, underscores, or hyphens.'],
        }

    @ddt.data(True, False)
    @patch("openedx.core.djangoapps.content_libraries.views.LibraryApiPagination.page_size", new=2)
    def test_list_library(self, is_indexing_enabled):
        """
        Test the /libraries API and its pagination
        """
        with override_settings(FEATURES={**settings.FEATURES, 'ENABLE_CONTENT_LIBRARY_INDEX': is_indexing_enabled}):
            lib1 = self._create_library(slug="some-slug-1", title="Existing Library")
            lib2 = self._create_library(slug="some-slug-2", title="Existing Library")
            if not is_indexing_enabled:
                lib1['num_blocks'] = lib2['num_blocks'] = None
                lib1['last_published'] = lib2['last_published'] = None
                lib1['has_unpublished_changes'] = lib2['has_unpublished_changes'] = None
                lib1['has_unpublished_deletes'] = lib2['has_unpublished_deletes'] = None

            result = self._list_libraries()
            assert len(result) == 2
            assert lib1 in result
            assert lib2 in result
            result = self._list_libraries({'pagination': 'true'})
            assert len(result['results']) == 2
            assert result['next'] is None

            # Create another library which causes number of libraries to exceed the page size
            self._create_library(slug="some-slug-3", title="Existing Library")
            # Verify that if `pagination` param isn't sent, API still honors the max page size.
            # This is for maintaining compatibility with older non pagination-aware clients.
            result = self._list_libraries()
            assert len(result) == 2

            # Pagination enabled:
            # Verify total elements and valid 'next' in page 1
            result = self._list_libraries({'pagination': 'true'})
            assert len(result['results']) == 2
            assert 'page=2' in result['next']
            assert 'pagination=true' in result['next']
            # Verify total elements and null 'next' in page 2
            result = self._list_libraries({'pagination': 'true', 'page': '2'})
            assert len(result['results']) == 1
            assert result['next'] is None

    @ddt.data(True, False)
    def test_library_filters(self, is_indexing_enabled):
        """
        Test the filters in the list libraries API
        """
        suffix = str(is_indexing_enabled)
        with override_settings(FEATURES={**settings.FEATURES, 'ENABLE_CONTENT_LIBRARY_INDEX': is_indexing_enabled}):
            self._create_library(
                slug=f"test-lib-filter-{suffix}-1", title="Fob", description=f"Bar-{suffix}", library_type=VIDEO,
            )
            self._create_library(
                slug=f"test-lib-filter-{suffix}-2", title=f"Library-Title-{suffix}-2", description=f"Bar-{suffix}-2",
            )
            self._create_library(
                slug=f"l3{suffix}", title=f"Library-Title-{suffix}-3", description="Description", library_type=VIDEO,
            )

            Organization.objects.get_or_create(
                short_name=f"org-test-{suffix}",
                defaults={"name": "Content Libraries Tachyon Exploration & Survey Team"},
            )
            self._create_library(
                slug=f"l4-{suffix}", title=f"Library-Title-{suffix}-4",
                description="Library-Description", org=f'org-test-{suffix}',
                library_type=VIDEO,
            )
            self._create_library(
                slug="l5", title=f"Library-Title-{suffix}-5", description="Library-Description",
                org=f'org-test-{suffix}',
            )

            assert len(self._list_libraries()) == 5
            assert len(self._list_libraries({'org': f'org-test-{suffix}'})) == 2
            assert len(self._list_libraries({'text_search': f'test-lib-filter-{suffix}'})) == 2
            assert len(self._list_libraries({'text_search': f'test-lib-filter-{suffix}', 'type': VIDEO})) == 1
            assert len(self._list_libraries({'text_search': f'library-title-{suffix}'})) == 4
            assert len(self._list_libraries({'text_search': f'library-title-{suffix}', 'type': VIDEO})) == 2
            assert len(self._list_libraries({'text_search': f'bar-{suffix}'})) == 2
            assert len(self._list_libraries({'text_search': f'org-test-{suffix}'})) == 2
            assert len(self._list_libraries({'org': f'org-test-{suffix}',
                                             'text_search': f'library-title-{suffix}-4'})) == 1
            assert len(self._list_libraries({'type': VIDEO})) == 3

    # General Content Library XBlock tests:

    def test_library_blocks(self):
        """
        Test the happy path of creating and working with XBlocks in a content
        library.
        """
        lib = self._create_library(slug="testlib1", title="A Test Library", description="Testing XBlocks")
        lib_id = lib["id"]
        assert lib['has_unpublished_changes'] is False

        # A library starts out empty:
        assert self._get_library_blocks(lib_id) == []

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
        assert 'def_key' in block_data

        # now the library should contain one block and have unpublished changes:
        assert self._get_library_blocks(lib_id) == [block_data]
        assert self._get_library(lib_id)['has_unpublished_changes'] is True

        # Publish the changes:
        self._commit_library_changes(lib_id)
        assert self._get_library(lib_id)['has_unpublished_changes'] is False
        # And now the block information should also show that block has no unpublished changes:
        block_data["has_unpublished_changes"] = False
        self.assertDictContainsEntries(self._get_library_block(block_id), block_data)
        assert self._get_library_blocks(lib_id) == [block_data]

        # Now update the block's OLX:
        orig_olx = self._get_library_block_olx(block_id)
        assert '<problem' in orig_olx
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
        assert self._get_library_block_olx(block_id) == new_olx
        # And the display name and "unpublished changes" status of the block should be updated:
        self.assertDictContainsEntries(self._get_library_block(block_id), {
            "display_name": "New Multi Choice Question",
            "has_unpublished_changes": True,
        })

        # Now view the XBlock's student_view (including draft changes):
        fragment = self._render_block_view(block_id, "student_view")
        assert 'resources' in fragment
        assert 'Blockstore is designed to store.' in fragment['content']

        # Also call a handler to make sure that's working:
        handler_url = self._get_block_handler_url(block_id, "xmodule_handler") + "problem_get"
        problem_get_response = self.client.get(handler_url)
        assert problem_get_response.status_code == 200
        assert 'You have used 0 of 5 attempts' in problem_get_response.content.decode('utf-8')

        # Now delete the block:
        assert self._get_library(lib_id)['has_unpublished_deletes'] is False
        self._delete_library_block(block_id)
        # Confirm it's deleted:
        self._render_block_view(block_id, "student_view", expect_response=404)
        self._get_library_block(block_id, expect_response=404)
        assert self._get_library(lib_id)['has_unpublished_deletes'] is True

        # Now revert all the changes back until the last publish:
        self._revert_library_changes(lib_id)
        assert self._get_library(lib_id)['has_unpublished_deletes'] is False
        assert self._get_library_block_olx(block_id) == orig_olx

        # fin

    def test_library_blocks_studio_view(self):
        """
        Test the happy path of working with an HTML XBlock in a the studio_view of a content library.
        """
        lib = self._create_library(slug="testlib2", title="A Test Library", description="Testing XBlocks")
        lib_id = lib["id"]
        assert lib['has_unpublished_changes'] is False

        # A library starts out empty:
        assert self._get_library_blocks(lib_id) == []

        # Add a 'html' XBlock to the library:
        block_data = self._add_block_to_library(lib_id, "html", "html1")
        self.assertDictContainsEntries(block_data, {
            "id": "lb:CL-TEST:testlib2:html:html1",
            "display_name": "Text",
            "block_type": "html",
            "has_unpublished_changes": True,
        })
        block_id = block_data["id"]
        # Confirm that the result contains a definition key, but don't check its value,
        # which for the purposes of these tests is an implementation detail.
        assert 'def_key' in block_data

        # now the library should contain one block and have unpublished changes:
        assert self._get_library_blocks(lib_id) == [block_data]
        assert self._get_library(lib_id)['has_unpublished_changes'] is True

        # Publish the changes:
        self._commit_library_changes(lib_id)
        assert self._get_library(lib_id)['has_unpublished_changes'] is False
        # And now the block information should also show that block has no unpublished changes:
        block_data["has_unpublished_changes"] = False
        self.assertDictContainsEntries(self._get_library_block(block_id), block_data)
        assert self._get_library_blocks(lib_id) == [block_data]

        # Now update the block's OLX:
        orig_olx = self._get_library_block_olx(block_id)
        assert '<html' in orig_olx
        new_olx = "<html><b>Hello world!</b></html>"
        self._set_library_block_olx(block_id, new_olx)
        # now reading it back, we should get that exact OLX (no change to whitespace etc.):
        assert self._get_library_block_olx(block_id) == new_olx
        # And the display name and "unpublished changes" status of the block should be updated:
        self.assertDictContainsEntries(self._get_library_block(block_id), {
            "display_name": "Text",
            "has_unpublished_changes": True,
        })

        # Now view the XBlock's studio view (including draft changes):
        fragment = self._render_block_view(block_id, "studio_view")
        assert 'resources' in fragment
        assert 'Hello world!' in fragment['content']

    @ddt.data(True, False)
    @patch("openedx.core.djangoapps.content_libraries.views.LibraryApiPagination.page_size", new=2)
    def test_list_library_blocks(self, is_indexing_enabled):
        """
        Test the /libraries/{lib_key_str}/blocks API and its pagination
        """
        with override_settings(FEATURES={**settings.FEATURES, 'ENABLE_CONTENT_LIBRARY_INDEX': is_indexing_enabled}):
            lib = self._create_library(slug="list_blocks-slug" + str(is_indexing_enabled), title="Library 1")
            block1 = self._add_block_to_library(lib["id"], "problem", "problem1")
            block2 = self._add_block_to_library(lib["id"], "unit", "unit1")

            self._add_block_to_library(lib["id"], "problem", "problem2", parent_block=block2["id"])

            result = self._get_library_blocks(lib["id"])
            assert len(result) == 2
            assert block1 in result

            result = self._get_library_blocks(lib["id"], {'pagination': 'true'})
            assert len(result['results']) == 2
            assert result['next'] is None

            self._add_block_to_library(lib["id"], "problem", "problem3")
            # Test pagination
            result = self._get_library_blocks(lib["id"])
            assert len(result) == 3
            result = self._get_library_blocks(lib["id"], {'pagination': 'true'})
            assert len(result['results']) == 2
            assert 'page=2' in result['next']
            assert 'pagination=true' in result['next']
            result = self._get_library_blocks(lib["id"], {'pagination': 'true', 'page': '2'})
            assert len(result['results']) == 1
            assert result['next'] is None

    @ddt.data(True, False)
    def test_library_blocks_filters(self, is_indexing_enabled):
        """
        Test the filters in the list libraries API
        """
        with override_settings(FEATURES={**settings.FEATURES, 'ENABLE_CONTENT_LIBRARY_INDEX': is_indexing_enabled}):
            lib = self._create_library(slug="test-lib-blocks" + str(is_indexing_enabled), title="Title")
            block1 = self._add_block_to_library(lib["id"], "problem", "foo-bar")
            self._add_block_to_library(lib["id"], "video", "vid-baz")
            self._add_block_to_library(lib["id"], "html", "html-baz")
            self._add_block_to_library(lib["id"], "problem", "foo-baz")
            self._add_block_to_library(lib["id"], "problem", "bar-baz")

            self._set_library_block_olx(block1["id"], "<problem display_name=\"DisplayName\"></problem>")

            assert len(self._get_library_blocks(lib['id'])) == 5
            assert len(self._get_library_blocks(lib['id'], {'text_search': 'Foo'})) == 2
            assert len(self._get_library_blocks(lib['id'], {'text_search': 'Display'})) == 1
            assert len(self._get_library_blocks(lib['id'], {'text_search': 'Video'})) == 1
            assert len(self._get_library_blocks(lib['id'], {'text_search': 'Foo', 'block_type': 'video'})) == 0
            assert len(self._get_library_blocks(lib['id'], {'text_search': 'Baz', 'block_type': 'video'})) == 1
            assert len(self._get_library_blocks(lib['id'], {'text_search': 'Baz', 'block_type': ['video', 'html']})) ==\
                   2
            assert len(self._get_library_blocks(lib['id'], {'block_type': 'video'})) == 1
            assert len(self._get_library_blocks(lib['id'], {'block_type': 'problem'})) == 3
            assert len(self._get_library_blocks(lib['id'], {'block_type': 'squirrel'})) == 0

    @ddt.data(
        ('video-problem', VIDEO, 'problem', 400),
        ('video-video', VIDEO, 'video', 200),
        ('problem-problem', PROBLEM, 'problem', 200),
        ('problem-video', PROBLEM, 'video', 400),
        ('complex-video', COMPLEX, 'video', 200),
        ('complex-problem', COMPLEX, 'problem', 200),
    )
    @ddt.unpack
    def test_library_blocks_type_constrained(self, slug, library_type, block_type, expect_response):
        """
        Test that type-constrained libraries enforce their constraint when adding an XBlock.
        """
        lib = self._create_library(
            slug=slug, title="A Test Library", description="Testing XBlocks", library_type=library_type,
        )
        lib_id = lib["id"]

        # Add a 'problem' XBlock to the library:
        self._add_block_to_library(lib_id, block_type, 'test-block', expect_response=expect_response)

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
        assert self._get_library_block_olx(unit_block['id']) ==\
               '<unit xblock-family="xblock.v1">\n  <xblock-include definition="html/html1"/>\n' \
               '  <xblock-include definition="problem/problem1"/>\n</unit>\n'

        # The unit can see and render its children:
        fragment = self._render_block_view(unit_block["id"], "student_view")
        assert 'Hello world' in fragment['content']
        assert 'What is an even number?' in fragment['content']

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
        never_added = UserFactory.create(username="Never", email="never@example.com")

        # Library CRUD #########################################################

        # Create a library, owned by "Admin"
        with self.as_user(admin):
            lib = self._create_library(slug="permtest", title="Permission Test Library", description="Testing")
            lib_id = lib["id"]
            # By default, "public learning" and public read access are disallowed.
            assert lib['allow_public_learning'] is False
            assert lib['allow_public_read'] is False

            # By default, the creator of a new library is the only admin
            data = self._get_library_team(lib_id)
            assert len(data) == 1
            self.assertDictContainsEntries(data[0], {
                "username": admin.username, "group_name": None, "access_level": "admin",
            })

            # Add the other users to the content library:
            self._set_user_access_level(lib_id, author.username, access_level="author")
            # Delete it, add it again.
            self._remove_user_access(lib_id, author.username)
            self._set_user_access_level(lib_id, author.username, access_level="author")
            # Add one of them via the email-based creation endpoint.
            self._add_user_by_email(lib_id, reader.email, access_level="read")
            self._set_group_access_level(lib_id, group.name, access_level="author")

            team_response = self._get_library_team(lib_id)
            assert len(team_response) == 4
            # We'll use this one later.
            reader_grant = {"username": reader.username, "group_name": None, "access_level": "read"}
            # The response should also always be sorted in a specific order (by username and group name):
            expected_response = [
                {"username": None, "group_name": "group1", "access_level": "author"},
                {"username": admin.username, "group_name": None, "access_level": "admin"},
                {"username": author.username, "group_name": None, "access_level": "author"},
                reader_grant,
            ]
            for entry, expected in zip(team_response, expected_response):
                self.assertDictContainsEntries(entry, expected)

        # A random user cannot get the library nor its team:
        with self.as_user(random_user):
            self._get_library(lib_id, expect_response=403)
            self._get_library_team(lib_id, expect_response=403)
            self._add_user_by_email(lib_id, never_added.email, access_level="read", expect_response=403)

        # But every authorized user can:
        for user in [admin, author, author_group_member]:
            with self.as_user(user):
                self._get_library(lib_id)
                data = self._get_library_team(lib_id)
                assert data == team_response
                data = self._get_user_access_level(lib_id, reader.username)
                assert data == {**reader_grant, 'username': 'Reader', 'email': 'reader@example.com'}

        # A user with only read permission can get data about the library but not the team:
        with self.as_user(reader):
            self._get_library(lib_id)
            self._get_library_team(lib_id, expect_response=403)
            self._get_user_access_level(lib_id, author.username, expect_response=403)
            self._add_user_by_email(lib_id, never_added.email, access_level="read", expect_response=403)

        # Users without admin access cannot delete the library nor change its team:
        for user in [author, reader, author_group_member, random_user]:
            with self.as_user(user):
                self._delete_library(lib_id, expect_response=403)
                self._set_user_access_level(lib_id, author.username, access_level="admin", expect_response=403)
                self._set_user_access_level(lib_id, admin.username, access_level=None, expect_response=403)
                self._set_user_access_level(lib_id, random_user.username, access_level="read", expect_response=403)
                self._remove_user_access(lib_id, admin.username, expect_response=403)
                self._add_user_by_email(lib_id, never_added.email, access_level="read", expect_response=403)

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
            assert data['description'] == 'Revised description'
            assert data['title'] == 'New Library Title'

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

    def test_no_lockout(self):
        """
        Test that administrators cannot be removed if they are the only administrator granted access.
        """
        admin = UserFactory.create(username="Admin", email="admin@example.com")
        successor = UserFactory.create(username="Successor", email="successor@example.com")
        with self.as_user(admin):
            lib = self._create_library(slug="permtest", title="Permission Test Library", description="Testing")
            # Fail to downgrade permissions.
            self._remove_user_access(lib_key=lib['id'], username=admin.username, expect_response=400)
            # Promote another user.
            self._set_user_access_level(
                lib_key=lib['id'], username=successor.username, access_level="admin",
            )
            self._remove_user_access(lib_key=lib['id'], username=admin.username)

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
        assert 'What is an odd number?' in fragment['content']
        assert 'What is an even number?' in fragment['content']
        assert 'What holds this XBlock?' in fragment['content']

        # Also check the API for retrieving links:
        links_created = self._get_library_links(lib_id)
        links_created.sort(key=lambda link: link["id"])
        assert len(links_created) == 2

        assert links_created[0]['id'] == 'problem_bank'
        assert links_created[0]['bundle_uuid'] == bank_lib['bundle_uuid']
        assert links_created[0]['version'] == 2
        assert links_created[0]['latest_version'] == 2
        assert links_created[0]['opaque_key'] == bank_lib_id

        assert links_created[1]['id'] == 'problem_bank_v1'
        assert links_created[1]['bundle_uuid'] == bank_lib['bundle_uuid']
        assert links_created[1]['version'] == 1
        assert links_created[1]['latest_version'] == 2
        assert links_created[1]['opaque_key'] == bank_lib_id

    def test_library_blocks_with_deleted_links(self):
        """
        Test that libraries can handle deleted links to bundles
        """
        # Create a problem bank:
        bank_lib = self._create_library(slug="problem_bank1X", title="Problem Bank")
        bank_lib_id = bank_lib["id"]
        # Add problem1 to the problem bank:
        p1 = self._add_block_to_library(bank_lib_id, "problem", "problem1X")
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

        # Create another problem bank:
        bank_lib2 = self._create_library(slug="problem_bank2", title="Problem Bank 2")
        bank_lib2_id = bank_lib2["id"]
        # Add problem1 to the problem bank:
        p2 = self._add_block_to_library(bank_lib2_id, "problem", "problem1X")
        self._set_library_block_olx(p2["id"], """
            <problem><multiplechoiceresponse>
                    <p>What is an odd number?</p>
                    <choicegroup type="MultipleChoice">
                        <choice correct="true">3</choice>
                        <choice correct="false">2</choice>
                    </choicegroup>
            </multiplechoiceresponse></problem>
        """)
        # Commit the changes, creating version 1:
        self._commit_library_changes(bank_lib2_id)

        lib = self._create_library(slug="problem_bank2X", title="Link Test Library")
        lib_id = lib["id"]
        # Link to the other libraries:
        self._link_to_library(lib_id, "problem_bank", bank_lib_id)
        self._link_to_library(lib_id, "problem_bank_v1", bank_lib2_id)

        # check the API for retrieving links:
        links_created = self._get_library_links(lib_id)
        links_created.sort(key=lambda link: link["id"])
        assert len(links_created) == 2

        assert links_created[0]['id'] == 'problem_bank'
        assert links_created[0]['bundle_uuid'] == bank_lib['bundle_uuid']
        assert links_created[0]['version'] == 1
        assert links_created[0]['latest_version'] == 1
        assert links_created[0]['opaque_key'] == bank_lib_id

        assert links_created[1]['id'] == 'problem_bank_v1'
        assert links_created[1]['bundle_uuid'] == bank_lib2['bundle_uuid']
        assert links_created[1]['version'] == 1
        assert links_created[1]['latest_version'] == 1
        assert links_created[1]['opaque_key'] == bank_lib2_id

        # Delete one of the linked bundles/libraries
        self._delete_library(bank_lib2_id)

        # update the cache so we're not getting cached links in the next step
        cache_key = 'bundle_version:{}:'.format(bank_lib['bundle_uuid'])
        cache.delete(cache_key)
        cache_key = 'bundle_version:{}:'.format(bank_lib2['bundle_uuid'])
        cache.delete(cache_key)

        links_created = self._get_library_links(lib_id)
        links_created.sort(key=lambda link: link["id"])
        assert len(links_created) == 2

        assert links_created[0]['id'] == 'problem_bank'
        assert links_created[0]['bundle_uuid'] == bank_lib['bundle_uuid']
        assert links_created[0]['version'] == 1
        assert links_created[0]['latest_version'] == 1
        assert links_created[0]['opaque_key'] == bank_lib_id

        # If a link has been deleted, the latest version will be 0,
        # and the opaque key will be `None`.
        assert links_created[1]['id'] == 'problem_bank_v1'
        assert links_created[1]['bundle_uuid'] == bank_lib2['bundle_uuid']
        assert links_created[1]['version'] == 1
        assert links_created[1]['latest_version'] == 0
        assert links_created[1]['opaque_key'] is None

    def test_library_blocks_limit(self):
        """
        Test that libraries don't allow more than specified blocks
        """
        with self.settings(MAX_BLOCKS_PER_CONTENT_LIBRARY=1):
            lib = self._create_library(slug="test_lib_limits", title="Limits Test Library", description="Testing XBlocks limits in a library")  # lint-amnesty, pylint: disable=line-too-long
            lib_id = lib["id"]
            block_data = self._add_block_to_library(lib_id, "unit", "unit1")
            # Second block should throw error
            self._add_block_to_library(lib_id, "problem", "problem1", expect_response=400)
            # Also check that limit applies to child blocks too
            self._add_block_to_library(lib_id, "html", "html1", parent_block=block_data['id'], expect_response=400)

    @ddt.data(
        ('complex-types', COMPLEX, False),
        ('video-types', VIDEO, True),
        ('problem-types', PROBLEM, True),
    )
    @ddt.unpack
    def test_block_types(self, slug, library_type, constrained):
        """
        Test that the permitted block types listing for a library change based on type.
        """
        lib = self._create_library(slug=slug, title='Test Block Types', library_type=library_type)
        types = self._get_library_block_types(lib['id'])
        if constrained:
            assert len(types) == 1
            assert types[0]['block_type'] == library_type
        else:
            assert len(types) > 1


@elasticsearch_test
class ContentLibrariesBlockstoreServiceTest(
    ContentLibrariesTestMixin,
    ContentLibrariesRestApiBlockstoreServiceTest,
):
    """
    General tests for Blockstore-based Content Libraries, using the standalone Blockstore service.
    """


@elasticsearch_test
class ContentLibrariesTest(
    ContentLibrariesTestMixin,
    ContentLibrariesRestApiTest,
):
    """
    General tests for Blockstore-based Content Libraries, using the installed Blockstore app.
    """


@ddt.ddt
class ContentLibraryXBlockValidationTest(APITestCase):
    """Tests only focused on service validation, no Blockstore needed."""

    @ddt.data(
        (URL_BLOCK_METADATA_URL, dict(block_key='totally_invalid_key')),
        (URL_BLOCK_RENDER_VIEW, dict(block_key='totally_invalid_key', view_name='random')),
        (URL_BLOCK_GET_HANDLER_URL, dict(block_key='totally_invalid_key', handler_name='random')),
    )
    @ddt.unpack
    def test_invalid_key(self, endpoint, endpoint_parameters):
        """Test all xblock related endpoints, when the key is invalid, return 404."""
        response = self.client.get(
            endpoint.format(**endpoint_parameters),
        )
        self.assertEqual(response.status_code, 404)
        msg = f"XBlock {endpoint_parameters.get('block_key')} does not exist, or you don't have permission to view it."
        self.assertEqual(response.json(), {
            'detail': msg,
        })

    def test_xblock_handler_invalid_key(self):
        """This endpoint is tested separately from the previous ones as it's not a DRF endpoint."""
        client = Client()
        response = client.get(URL_BLOCK_XBLOCK_HANDLER.format(**dict(
            block_key='totally_invalid_key',
            handler_name='random',
            user_id='random',
            secure_token='random',
        )))
        self.assertEqual(response.status_code, 404)

    def test_not_found_fails_correctly(self):
        """Test fails with 404 when xblock key is valid but not found."""
        valid_not_found_key = 'lb:valid:key:video:1'
        response = self.client.get(URL_BLOCK_METADATA_URL.format(block_key=valid_not_found_key))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {
            'detail': f"XBlock {valid_not_found_key} does not exist, or you don't have permission to view it.",
        })
