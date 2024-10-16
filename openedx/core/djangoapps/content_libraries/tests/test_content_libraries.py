"""
Tests for Learning-Core-based Content Libraries
"""
from datetime import datetime, timezone
from unittest import skip
from unittest.mock import Mock, patch
from uuid import uuid4

import ddt
from django.contrib.auth.models import Group
from django.test.client import Client
from freezegun import freeze_time
from opaque_keys.edx.locator import LibraryLocatorV2, LibraryUsageLocatorV2
from openedx_events.content_authoring.data import ContentLibraryData, LibraryBlockData
from openedx_events.content_authoring.signals import (
    CONTENT_LIBRARY_CREATED,
    CONTENT_LIBRARY_DELETED,
    CONTENT_LIBRARY_UPDATED,
    LIBRARY_BLOCK_CREATED,
    LIBRARY_BLOCK_DELETED,
    LIBRARY_BLOCK_UPDATED
)
from openedx_events.tests.utils import OpenEdxEventsTestMixin
from organizations.models import Organization
from rest_framework.test import APITestCase

from common.djangoapps.student.tests.factories import UserFactory
from openedx.core.djangoapps.content_libraries.constants import CC_4_BY, COMPLEX, PROBLEM, VIDEO
from openedx.core.djangoapps.content_libraries.tests.base import (
    URL_BLOCK_GET_HANDLER_URL,
    URL_BLOCK_METADATA_URL,
    URL_BLOCK_RENDER_VIEW,
    URL_BLOCK_XBLOCK_HANDLER,
    ContentLibrariesRestApiTest
)
from openedx.core.djangoapps.xblock import api as xblock_api
from openedx.core.djangolib.testing.utils import skip_unless_cms


@skip_unless_cms
@ddt.ddt
class ContentLibrariesTestCase(ContentLibrariesRestApiTest, OpenEdxEventsTestMixin):
    """
    General tests for Learning-Core-based Content Libraries

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
    ENABLED_OPENEDX_EVENTS = [
        CONTENT_LIBRARY_CREATED.event_type,
        CONTENT_LIBRARY_DELETED.event_type,
        CONTENT_LIBRARY_UPDATED.event_type,
        LIBRARY_BLOCK_CREATED.event_type,
        LIBRARY_BLOCK_DELETED.event_type,
        LIBRARY_BLOCK_UPDATED.event_type,
    ]

    @classmethod
    def setUpClass(cls):
        """
        Set up class method for the Test class.

        TODO: It's unclear why we need to call start_events_isolation ourselves rather than relying on
              OpenEdxEventsTestMixin.setUpClass to handle it. It fails it we don't, and many other test cases do it,
              so we're following a pattern here. But that pattern doesn't really make sense.
        """
        super().setUpClass()
        cls.start_events_isolation()

    def test_library_crud(self):
        """
        Test Create, Read, Update, and Delete of a Content Library

        Tests with some non-ASCII chars in slug, title, description.
        """
        # Create:
        lib = self._create_library(
            slug="téstlꜟط", title="A Tést Lꜟطrary", description="Just Téstꜟng", license_type=CC_4_BY,
        )
        expected_data = {
            "id": "lib:CL-TEST:téstlꜟط",
            "org": "CL-TEST",
            "slug": "téstlꜟط",
            "title": "A Tést Lꜟطrary",
            "description": "Just Téstꜟng",
            "version": 0,
            "type": COMPLEX,
            "license": CC_4_BY,
            "has_unpublished_changes": False,
            "has_unpublished_deletes": False,
        }

        self.assertDictContainsEntries(lib, expected_data)
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

        # Try to create a library+bundle with a duplicate slug
        response = self._create_library(slug="some-slug", title="Duplicate Library", expect_response=400)
        assert response == {
            'slug': 'A library with that ID already exists.',
        }

        response = self._create_library(slug="Invalid Slug!", title="Library with Bad Slug", expect_response=400)
        assert response == {
            'slug': ['Enter a valid “slug” consisting of Unicode letters, numbers, underscores, or hyphens.'],
        }

    @skip("This endpoint shouldn't support num_blocks and has_unpublished_*.")
    @patch("openedx.core.djangoapps.content_libraries.views.LibraryRootView.pagination_class.page_size", new=2)
    def test_list_library(self):
        """
        Test the /libraries API and its pagination

        TODO: This test will technically pass, but it's not really meaningful
        because we don't have real data behind num_blocks, last_published,
        has_published_changes, and has_unpublished_deletes. The has_* in
        particular are going to be expensive to compute, particularly if we have
        many large libraries. We also don't use that data for the library list
        page yet.

        We're looking at re-doing a lot of the UX right now, and so I'm holding
        off on making deeper changes. We should either make sure we don't need
        those fields and remove them from the returned results, or else we
        should figure out how to make them more performant.

        I've marked this as @skip to flag it for future review.
        """
        lib1 = self._create_library(slug="some-slug-1", title="Existing Library")
        lib2 = self._create_library(slug="some-slug-2", title="Existing Library")
        lib1['num_blocks'] = lib2['num_blocks'] = 0
        lib1['last_published'] = lib2['last_published'] = None
        lib1['version'] = lib2['version'] = None
        lib1['has_unpublished_changes'] = lib2['has_unpublished_changes'] = False
        lib1['has_unpublished_deletes'] = lib2['has_unpublished_deletes'] = False

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

    def test_library_filters(self):
        """
        Test the filters in the list libraries API
        """
        self._create_library(
            slug="test-lib-filter-1", title="Fob", description="Bar", library_type=VIDEO,
        )
        self._create_library(
            slug="test-lib-filter-2", title="Library-Title-2", description="Bar-2",
        )
        self._create_library(
            slug="l3", title="Library-Title-3", description="Description", library_type=VIDEO,
        )

        Organization.objects.get_or_create(
            short_name="org-test",
            defaults={"name": "Content Libraries Tachyon Exploration & Survey Team"},
        )
        self._create_library(
            slug="l4", title="Library-Title-4",
            description="Library-Description", org='org-test',
            library_type=VIDEO,
        )
        self._create_library(
            slug="l5", title="Library-Title-5", description="Library-Description",
            org='org-test',
        )

        assert len(self._list_libraries()) == 5
        assert len(self._list_libraries({'org': 'org-test'})) == 2
        assert len(self._list_libraries({'text_search': 'test-lib-filter'})) == 2
        assert len(self._list_libraries({'text_search': 'test-lib-filter', 'type': VIDEO})) == 1
        assert len(self._list_libraries({'text_search': 'library-title'})) == 4
        assert len(self._list_libraries({'text_search': 'library-title', 'type': VIDEO})) == 2
        assert len(self._list_libraries({'text_search': 'bar'})) == 2
        assert len(self._list_libraries({'text_search': 'org-test'})) == 2
        assert len(self._list_libraries({'org': 'org-test',
                                         'text_search': 'library-title-4'})) == 1
        assert len(self._list_libraries({'type': VIDEO})) == 3

        self.assertOrderEqual(
            self._list_libraries({'order': 'title'}),
            ["test-lib-filter-1", "test-lib-filter-2", "l3", "l4", "l5"],
        )
        self.assertOrderEqual(
            self._list_libraries({'order': '-title'}),
            ["l5", "l4", "l3", "test-lib-filter-2", "test-lib-filter-1"],
        )
        self.assertOrderEqual(
            self._list_libraries({'order': 'created'}),
            ["test-lib-filter-1", "test-lib-filter-2", "l3", "l4", "l5"],
        )
        self.assertOrderEqual(
            self._list_libraries({'order': '-created'}),
            ["l5", "l4", "l3", "test-lib-filter-2", "test-lib-filter-1"],
        )
        # An invalid order doesn't apply any specific ordering to the result, so just
        # check if successfully returned libraries
        assert len(self._list_libraries({'order': 'invalid'})) == 5
        assert len(self._list_libraries({'order': '-invalid'})) == 5

    # General Content Library XBlock tests:

    def test_library_blocks(self):
        """
        Test the happy path of creating and working with XBlocks in a content
        library.

        Tests with some non-ASCII chars in slugs, titles, descriptions.
        """
        lib = self._create_library(slug="téstlꜟط", title="A Tést Lꜟطrary", description="Tésting XBlocks")
        lib_id = lib["id"]
        assert lib['has_unpublished_changes'] is False

        # A library starts out empty:
        assert self._get_library_blocks(lib_id)['results'] == []

        # Add a 'problem' XBlock to the library:
        create_date = datetime(2024, 6, 6, 6, 6, 6, tzinfo=timezone.utc)
        with freeze_time(create_date):
            block_data = self._add_block_to_library(lib_id, "problem", "ࠒröblæm1")
        self.assertDictContainsEntries(block_data, {
            "id": "lb:CL-TEST:téstlꜟط:problem:ࠒröblæm1",
            "display_name": "Blank Problem",
            "block_type": "problem",
            "has_unpublished_changes": True,
            "last_published": None,
            "published_by": None,
            "last_draft_created": create_date.isoformat().replace('+00:00', 'Z'),
            "last_draft_created_by": "Bob",
        })
        block_id = block_data["id"]
        # Confirm that the result contains a definition key, but don't check its value,
        # which for the purposes of these tests is an implementation detail.
        assert 'def_key' in block_data

        # now the library should contain one block and have unpublished changes:
        assert self._get_library_blocks(lib_id)['results'] == [block_data]
        assert self._get_library(lib_id)['has_unpublished_changes'] is True

        # Publish the changes:
        publish_date = datetime(2024, 7, 7, 7, 7, 7, tzinfo=timezone.utc)
        with freeze_time(publish_date):
            self._commit_library_changes(lib_id)
        assert self._get_library(lib_id)['has_unpublished_changes'] is False
        # And now the block information should also show that block has no unpublished changes:
        block_data["has_unpublished_changes"] = False
        block_data["last_published"] = publish_date.isoformat().replace('+00:00', 'Z')
        block_data["published_by"] = "Bob"
        self.assertDictContainsEntries(self._get_library_block(block_id), block_data)
        assert self._get_library_blocks(lib_id)['results'] == [block_data]

        # Now update the block's OLX:
        orig_olx = self._get_library_block_olx(block_id)
        assert '<problem' in orig_olx
        new_olx = """
        <problem display_name="New Multi Choice Question" max_attempts="5">
            <multiplechoiceresponse>
                <p>This is a normal capa problem with unicode 🔥. It has "maximum attempts" set to **5**.</p>
                <label>Learning Core is designed to store.</label>
                <choicegroup type="MultipleChoice">
                    <choice correct="false">XBlock metadata only</choice>
                    <choice correct="true">XBlock data/metadata and associated static asset files</choice>
                    <choice correct="false">Static asset files for XBlocks and courseware</choice>
                    <choice correct="false">XModule metadata only</choice>
                </choicegroup>
            </multiplechoiceresponse>
        </problem>
        """.strip()
        update_date = datetime(2024, 8, 8, 8, 8, 8, tzinfo=timezone.utc)
        with freeze_time(update_date):
            self._set_library_block_olx(block_id, new_olx)
        # now reading it back, we should get that exact OLX (no change to whitespace etc.):
        assert self._get_library_block_olx(block_id) == new_olx
        # And the display name and "unpublished changes" status of the block should be updated:
        self.assertDictContainsEntries(self._get_library_block(block_id), {
            "display_name": "New Multi Choice Question",
            "has_unpublished_changes": True,
            "last_draft_created": update_date.isoformat().replace('+00:00', 'Z')
        })

        # Now view the XBlock's student_view (including draft changes):
        fragment = self._render_block_view(block_id, "student_view")
        assert 'resources' in fragment
        assert 'Learning Core is designed to store.' in fragment['content']

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
        assert self._get_library_blocks(lib_id)['results'] == []

        # Add a 'html' XBlock to the library:
        create_date = datetime(2024, 6, 6, 6, 6, 6, tzinfo=timezone.utc)
        with freeze_time(create_date):
            block_data = self._add_block_to_library(lib_id, "html", "html1")
        self.assertDictContainsEntries(block_data, {
            "id": "lb:CL-TEST:testlib2:html:html1",
            "display_name": "Text",
            "block_type": "html",
            "has_unpublished_changes": True,
            "last_published": None,
            "published_by": None,
            "last_draft_created": create_date.isoformat().replace('+00:00', 'Z'),
            "last_draft_created_by": "Bob",
        })
        block_id = block_data["id"]

        # now the library should contain one block and have unpublished changes:
        assert self._get_library_blocks(lib_id)['results'] == [block_data]
        assert self._get_library(lib_id)['has_unpublished_changes'] is True

        # Publish the changes:
        publish_date = datetime(2024, 7, 7, 7, 7, 7, tzinfo=timezone.utc)
        with freeze_time(publish_date):
            self._commit_library_changes(lib_id)
        assert self._get_library(lib_id)['has_unpublished_changes'] is False
        # And now the block information should also show that block has no unpublished changes:
        block_data["has_unpublished_changes"] = False
        block_data["last_published"] = publish_date.isoformat().replace('+00:00', 'Z')
        block_data["published_by"] = "Bob"
        self.assertDictContainsEntries(self._get_library_block(block_id), block_data)
        assert self._get_library_blocks(lib_id)['results'] == [block_data]

        # Now update the block's OLX:
        orig_olx = self._get_library_block_olx(block_id)
        assert '<html' in orig_olx
        new_olx = "<html><b>Hello world!</b></html>"

        update_date = datetime(2024, 8, 8, 8, 8, 8, tzinfo=timezone.utc)
        with freeze_time(update_date):
            self._set_library_block_olx(block_id, new_olx)
        # now reading it back, we should get that exact OLX (no change to whitespace etc.):
        assert self._get_library_block_olx(block_id) == new_olx
        # And the display name and "unpublished changes" status of the block should be updated:
        self.assertDictContainsEntries(self._get_library_block(block_id), {
            "display_name": "Text",
            "has_unpublished_changes": True,
            "last_draft_created": update_date.isoformat().replace('+00:00', 'Z')
        })

        # Now view the XBlock's studio view (including draft changes):
        fragment = self._render_block_view(block_id, "studio_view")
        assert 'resources' in fragment
        assert 'Hello world!' in fragment['content']

    @patch("openedx.core.djangoapps.content_libraries.views.LibraryBlocksView.pagination_class.page_size", new=2)
    def test_list_library_blocks(self):
        """
        Test the /libraries/{lib_key_str}/blocks API and its pagination
        """
        lib = self._create_library(slug="list_blocks-slug", title="Library 1")
        block1 = self._add_block_to_library(lib["id"], "problem", "problem1")
        self._add_block_to_library(lib["id"], "unit", "unit1")

        response = self._get_library_blocks(lib["id"])
        result = response['results']
        assert len(response['results']) == 2
        assert block1 in result
        assert response['next'] is None

        self._add_block_to_library(lib["id"], "problem", "problem3")

        # Test pagination
        result = self._get_library_blocks(lib["id"])
        assert len(result['results']) == 2

        assert 'page=2' in result['next']
        result = self._get_library_blocks(lib["id"], {'page': '2'})
        assert len(result['results']) == 1
        assert result['next'] is None

    def test_library_blocks_filters(self):
        """
        Test the filters in the list libraries API
        """
        lib = self._create_library(slug="test-lib-blocks", title="Title")
        block1 = self._add_block_to_library(lib["id"], "problem", "foo-bar")
        self._add_block_to_library(lib["id"], "video", "vid-baz")
        self._add_block_to_library(lib["id"], "html", "html-baz")
        self._add_block_to_library(lib["id"], "problem", "foo-baz")
        self._add_block_to_library(lib["id"], "problem", "bar-baz")

        self._set_library_block_olx(block1["id"], "<problem display_name=\"DisplayName\"></problem>")

        assert len(self._get_library_blocks(lib['id'])['results']) == 5
        assert len(self._get_library_blocks(lib['id'], {'text_search': 'Foo'})['results']) == 2
        assert len(self._get_library_blocks(lib['id'], {'text_search': 'Display'})['results']) == 1
        assert len(self._get_library_blocks(lib['id'], {'text_search': 'Video'})['results']) == 1
        assert len(self._get_library_blocks(lib['id'], {'text_search': 'Foo', 'block_type': 'video'})['results']) == 0
        assert len(self._get_library_blocks(lib['id'], {'text_search': 'Baz', 'block_type': 'video'})['results']) == 1
        assert 2 == len(
            self._get_library_blocks(
                lib['id'],
                {'text_search': 'Baz', 'block_type': ['video', 'html']}
            )['results']
        )
        assert len(self._get_library_blocks(lib['id'], {'block_type': 'video'})['results']) == 1
        assert len(self._get_library_blocks(lib['id'], {'block_type': 'problem'})['results']) == 3
        assert len(self._get_library_blocks(lib['id'], {'block_type': 'squirrel'})['results']) == 0

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

    def test_library_not_found(self):
        """Test that requests fail with 404 when the library does not exist"""
        valid_not_found_key = 'lb:valid:key:video:1'
        response = self.client.get(URL_BLOCK_METADATA_URL.format(block_key=valid_not_found_key))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {
            'detail': "Content Library 'lib:valid:key' does not exist",
        })

    def test_block_not_found(self):
        """Test that requests fail with 404 when the library exists but the XBlock does not"""
        lib = self._create_library(
            slug="test_lib_block_event_delete",
            title="Event Test Library",
            description="Testing event in library"
        )
        library_key = LibraryLocatorV2.from_string(lib['id'])
        non_existent_block_key = LibraryUsageLocatorV2(lib_key=library_key, block_type='video', usage_id='123')
        response = self.client.get(URL_BLOCK_METADATA_URL.format(block_key=non_existent_block_key))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {
            'detail': f"The component '{non_existent_block_key}' does not exist.",
        })

    # Test that permissions are enforced for content libraries

    def test_library_permissions(self):  # pylint: disable=too-many-statements
        """
        Test that permissions are enforced for content libraries, and that
        permissions can be read and manipulated using the REST API (which in
        turn tests the python API).

        This is a single giant test case, because that optimizes for the fastest
        test run time, even though it can make debugging failures harder.

        TODO: The asset permissions part of this test have been commented out
        for now. These should be re-enabled after we re-implement them over
        Learning Core data models.
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
            self._get_library_block_fields(block3_key, expect_response=403)
            self._get_library_block_assets(block3_key, expect_response=403)
            self._get_library_block_asset(block3_key, file_name="static/whatever.png", expect_response=403)
            # Nor can they preview the block:
            self._render_block_view(block3_key, view_name="student_view", expect_response=403)
        # But if we grant allow_public_read, then they can:
        with self.as_user(admin):
            self._update_library(lib_id, allow_public_read=True)
            self._set_library_block_asset(block3_key, "static/whatever.png", b"data")
        with self.as_user(random_user):
            self._get_library_block_olx(block3_key)
            self._render_block_view(block3_key, view_name="student_view")
            f = self._get_library_block_fields(block3_key)
            # self._get_library_block_assets(block3_key)
            # self._get_library_block_asset(block3_key, file_name="whatever.png")

        # Users without authoring permission cannot edit nor delete XBlocks:
        for user in [reader, random_user]:
            with self.as_user(user):
                self._set_library_block_olx(block3_key, "<problem/>", expect_response=403)
                self._set_library_block_fields(block3_key, {"data": "<problem />", "metadata": {}}, expect_response=403)
                self._set_library_block_asset(block3_key, "static/test.txt", b"data", expect_response=403)
                self._delete_library_block(block3_key, expect_response=403)
                self._commit_library_changes(lib_id, expect_response=403)
                self._revert_library_changes(lib_id, expect_response=403)

        # But users with author permission can:
        with self.as_user(author_group_member):
            olx = self._get_library_block_olx(block3_key)
            self._set_library_block_olx(block3_key, olx)
            self._set_library_block_fields(block3_key, {"data": olx, "metadata": {}})
            self._get_library_block_assets(block3_key)
            self._set_library_block_asset(block3_key, "static/test.txt", b"data")
            self._get_library_block_asset(block3_key, file_name="static/test.txt")
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

    def test_library_blocks_limit(self):
        """
        Test that libraries don't allow more than specified blocks
        """
        with self.settings(MAX_BLOCKS_PER_CONTENT_LIBRARY=1):
            lib = self._create_library(
                slug="test_lib_limits",
                title="Limits Test Library",
                description="Testing XBlocks limits in a library"
            )
            lib_id = lib["id"]
            self._add_block_to_library(lib_id, "unit", "unit1")
            # Second block should throw error
            self._add_block_to_library(lib_id, "problem", "problem1", expect_response=400)

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

    def test_content_library_create_event(self):
        """
        Check that CONTENT_LIBRARY_CREATED event is sent when a content library is created.
        """
        event_receiver = Mock()
        CONTENT_LIBRARY_CREATED.connect(event_receiver)
        lib = self._create_library(
            slug="test_lib_event_create",
            title="Event Test Library",
            description="Testing event in library"
        )
        library_key = LibraryLocatorV2.from_string(lib['id'])

        event_receiver.assert_called_once()
        self.assertDictContainsSubset(
            {
                "signal": CONTENT_LIBRARY_CREATED,
                "sender": None,
                "content_library": ContentLibraryData(
                    library_key=library_key,
                    update_blocks=False,
                ),
            },
            event_receiver.call_args.kwargs
        )

    def test_content_library_update_event(self):
        """
        Check that CONTENT_LIBRARY_UPDATED event is sent when a content library is updated.
        """
        event_receiver = Mock()
        CONTENT_LIBRARY_UPDATED.connect(event_receiver)
        lib = self._create_library(
            slug="test_lib_event_update",
            title="Event Test Library",
            description="Testing event in library"
        )

        lib2 = self._update_library(lib["id"], title="New Title")
        library_key = LibraryLocatorV2.from_string(lib2['id'])

        event_receiver.assert_called_once()
        self.assertDictContainsSubset(
            {
                "signal": CONTENT_LIBRARY_UPDATED,
                "sender": None,
                "content_library": ContentLibraryData(
                    library_key=library_key,
                    update_blocks=False,
                ),
            },
            event_receiver.call_args.kwargs
        )

    def test_content_library_delete_event(self):
        """
        Check that CONTENT_LIBRARY_DELETED event is sent when a content library is deleted.
        """
        event_receiver = Mock()
        CONTENT_LIBRARY_DELETED.connect(event_receiver)
        lib = self._create_library(
            slug="test_lib_event_delete",
            title="Event Test Library",
            description="Testing event in library"
        )
        library_key = LibraryLocatorV2.from_string(lib['id'])

        self._delete_library(lib["id"])

        event_receiver.assert_called_once()
        self.assertDictContainsSubset(
            {
                "signal": CONTENT_LIBRARY_DELETED,
                "sender": None,
                "content_library": ContentLibraryData(
                    library_key=library_key,
                    update_blocks=False,
                ),
            },
            event_receiver.call_args.kwargs
        )

    def test_library_block_create_event(self):
        """
        Check that LIBRARY_BLOCK_CREATED event is sent when a library block is created.
        """
        event_receiver = Mock()
        LIBRARY_BLOCK_CREATED.connect(event_receiver)
        lib = self._create_library(
            slug="test_lib_block_event_create",
            title="Event Test Library",
            description="Testing event in library"
        )
        lib_id = lib["id"]
        self._add_block_to_library(lib_id, "problem", "problem1")

        library_key = LibraryLocatorV2.from_string(lib_id)
        usage_key = LibraryUsageLocatorV2(
            lib_key=library_key,
            block_type="problem",
            usage_id="problem1"
        )

        event_receiver.assert_called_once()
        self.assertDictContainsSubset(
            {
                "signal": LIBRARY_BLOCK_CREATED,
                "sender": None,
                "library_block": LibraryBlockData(
                    library_key=library_key,
                    usage_key=usage_key
                ),
            },
            event_receiver.call_args.kwargs
        )

    def test_library_block_olx_update_event(self):
        """
        Check that LIBRARY_BLOCK_CREATED event is sent when the OLX source is updated.
        """
        event_receiver = Mock()
        LIBRARY_BLOCK_UPDATED.connect(event_receiver)
        lib = self._create_library(
            slug="test_lib_block_event_olx_update",
            title="Event Test Library",
            description="Testing event in library"
        )
        lib_id = lib["id"]

        library_key = LibraryLocatorV2.from_string(lib_id)

        block = self._add_block_to_library(lib_id, "problem", "problem1")
        block_id = block["id"]
        usage_key = LibraryUsageLocatorV2(
            lib_key=library_key,
            block_type="problem",
            usage_id="problem1"
        )

        new_olx = """
        <problem display_name="New Multi Choice Question" max_attempts="5">
            <multiplechoiceresponse>
                <p>This is a normal capa problem with unicode 🔥. It has "maximum attempts" set to **5**.</p>
                <label>Learning Core is designed to store.</label>
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

        event_receiver.assert_called_once()
        self.assertDictContainsSubset(
            {
                "signal": LIBRARY_BLOCK_UPDATED,
                "sender": None,
                "library_block": LibraryBlockData(
                    library_key=library_key,
                    usage_key=usage_key
                ),
            },
            event_receiver.call_args.kwargs
        )

    def test_library_block_add_asset_update_event(self):
        """
        Check that LIBRARY_BLOCK_CREATED event is sent when a static asset is
        uploaded associated with the XBlock.
        """
        event_receiver = Mock()
        LIBRARY_BLOCK_UPDATED.connect(event_receiver)
        lib = self._create_library(
            slug="test_lib_block_event_add_asset_update",
            title="Event Test Library",
            description="Testing event in library"
        )
        lib_id = lib["id"]

        library_key = LibraryLocatorV2.from_string(lib_id)

        block = self._add_block_to_library(lib_id, "unit", "u1")
        block_id = block["id"]
        self._set_library_block_asset(block_id, "static/test.txt", b"data")

        usage_key = LibraryUsageLocatorV2(
            lib_key=library_key,
            block_type="unit",
            usage_id="u1"
        )

        event_receiver.assert_called_once()
        self.assertDictContainsSubset(
            {
                "signal": LIBRARY_BLOCK_UPDATED,
                "sender": None,
                "library_block": LibraryBlockData(
                    library_key=library_key,
                    usage_key=usage_key
                ),
            },
            event_receiver.call_args.kwargs
        )

    def test_library_block_del_asset_update_event(self):
        """
        Check that LIBRARY_BLOCK_CREATED event is sent when a static asset is
        removed from XBlock.
        """
        event_receiver = Mock()
        LIBRARY_BLOCK_UPDATED.connect(event_receiver)
        lib = self._create_library(
            slug="test_lib_block_event_del_asset_update",
            title="Event Test Library",
            description="Testing event in library"
        )
        lib_id = lib["id"]

        library_key = LibraryLocatorV2.from_string(lib_id)

        block = self._add_block_to_library(lib_id, "unit", "u1")
        block_id = block["id"]
        self._set_library_block_asset(block_id, "static/test.txt", b"data")

        self._delete_library_block_asset(block_id, 'static/text.txt')

        usage_key = LibraryUsageLocatorV2(
            lib_key=library_key,
            block_type="unit",
            usage_id="u1"
        )

        event_receiver.assert_called()
        self.assertDictContainsSubset(
            {
                "signal": LIBRARY_BLOCK_UPDATED,
                "sender": None,
                "library_block": LibraryBlockData(
                    library_key=library_key,
                    usage_key=usage_key
                ),
            },
            event_receiver.call_args.kwargs
        )

    def test_library_block_delete_event(self):
        """
        Check that LIBRARY_BLOCK_DELETED event is sent when a content library is deleted.
        """
        event_receiver = Mock()
        LIBRARY_BLOCK_DELETED.connect(event_receiver)
        lib = self._create_library(
            slug="test_lib_block_event_delete",
            title="Event Test Library",
            description="Testing event in library"
        )

        lib_id = lib["id"]
        library_key = LibraryLocatorV2.from_string(lib_id)

        block = self._add_block_to_library(lib_id, "problem", "problem1")
        block_id = block['id']

        usage_key = LibraryUsageLocatorV2(
            lib_key=library_key,
            block_type="problem",
            usage_id="problem1"
        )

        self._delete_library_block(block_id)

        event_receiver.assert_called()
        self.assertDictContainsSubset(
            {
                "signal": LIBRARY_BLOCK_DELETED,
                "sender": None,
                "library_block": LibraryBlockData(
                    library_key=library_key,
                    usage_key=usage_key
                ),
            },
            event_receiver.call_args.kwargs
        )

    def test_library_paste_clipboard(self):
        """
        Check the a new block is created in the library after pasting from clipboard.
        The content of the new block should match the content of the block in the clipboard.
        """
        # Importing here since this was failing when tests ran in the LMS
        from openedx.core.djangoapps.content_staging.api import save_xblock_to_user_clipboard

        # Create user to perform tests on
        author = UserFactory.create(username="Author", email="author@example.com")
        with self.as_user(author):
            lib = self._create_library(
                slug="test_lib_paste_clipboard",
                title="Paste Clipboard Test Library",
                description="Testing pasting clipboard in library"
            )
            lib_id = lib["id"]

            # Add a 'problem' XBlock to the library:
            block_data = self._add_block_to_library(lib_id, "problem", "problem1")

            # Get the usage_key of the created block
            library_key = LibraryLocatorV2.from_string(lib_id)
            usage_key = LibraryUsageLocatorV2(
                lib_key=library_key,
                block_type="problem",
                usage_id="problem1"
            )

            # Get the XBlock created in the previous step
            block = xblock_api.load_block(usage_key, user=author)

            # Copy the block to the user's clipboard
            save_xblock_to_user_clipboard(block, author.id)

            # Paste the content of the clipboard into the library
            pasted_block_id = str(uuid4())
            paste_data = self._paste_clipboard_content_in_library(lib_id, pasted_block_id)

            # Check that the new block was created after the paste and it's content matches
            # the the block in the clipboard
            self.assertDictContainsEntries(self._get_library_block(paste_data["id"]), {
                **block_data,
                "last_draft_created_by": None,
                "last_draft_created": paste_data["last_draft_created"],
                "created": paste_data["created"],
                "modified": paste_data["modified"],
                "id": f"lb:CL-TEST:test_lib_paste_clipboard:problem:{pasted_block_id}",
            })


@ddt.ddt
class ContentLibraryXBlockValidationTest(APITestCase):
    """Tests only focused on service validation, no Learning Core interactions here."""

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
