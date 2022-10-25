"""
Tests for library tools service.
"""
from unittest.mock import patch

from opaque_keys.edx.keys import UsageKey
from openedx.core.djangoapps.content_libraries import api as library_api
from openedx.core.djangoapps.content_libraries.tests.base import ContentLibrariesRestApiTest
from openedx.core.djangoapps.xblock.api import load_block
from common.djangoapps.student.roles import CourseInstructorRole
from xmodule.library_tools import LibraryToolsService
from xmodule.modulestore.tests.factories import CourseFactory, LibraryFactory
from xmodule.modulestore.tests.utils import MixedSplitTestCase


class LibraryToolsServiceTest(MixedSplitTestCase):
    """
    Tests for library service.
    """

    def setUp(self):
        super().setUp()
        self.tools = LibraryToolsService(self.store, self.user_id)

    def test_list_available_libraries(self):
        """
        Test listing of libraries.
        """
        _ = LibraryFactory.create(modulestore=self.store)
        all_libraries = self.tools.list_available_libraries()
        assert all_libraries
        assert len(all_libraries) == 1

    @patch('xmodule.modulestore.split_mongo.split.SplitMongoModuleStore.get_library_summaries')
    def test_list_available_libraries_fetch(self, mock_get_library_summaries):
        """
        Test that library list is compiled using light weight library summary objects.
        """
        _ = self.tools.list_available_libraries()
        assert mock_get_library_summaries.called


class ContentLibraryToolsTest(MixedSplitTestCase, ContentLibrariesRestApiTest):
    """
    Tests for LibraryToolsService which interact with blockstore-based content libraries
    """
    def setUp(self):
        super().setUp()
        self.tools = LibraryToolsService(self.store, self.user.id)

    def test_import_from_blockstore(self):
        # Create a blockstore content library
        library = self._create_library(slug="testlib1_import", title="A Test Library", description="Testing XBlocks")
        # Create a unit block with an HTML block in it.
        unit_block_id = self._add_block_to_library(library["id"], "unit", "unit1")["id"]
        html_block_id = self._add_block_to_library(library["id"], "html", "html1", parent_block=unit_block_id)["id"]
        html_block = load_block(UsageKey.from_string(html_block_id), self.user)
        # Add assets and content to the HTML block
        self._set_library_block_asset(html_block_id, "test.txt", b"data", expect_response=200)
        self._set_library_block_olx(html_block_id, '<html><a href="/static/test.txt">Hello world</a></html>')

        # Create a modulestore course
        course = CourseFactory.create(modulestore=self.store, user_id=self.user.id)
        CourseInstructorRole(course.id).add_users(self.user)
        # Add Source from library block to the course
        sourced_block = self.make_block("library_sourced", course, user_id=self.user.id)

        # Import the unit block from the library to the course
        self.tools.import_from_blockstore(sourced_block, [unit_block_id])

        # Verify imported block with its children
        assert len(sourced_block.children) == 1
        assert sourced_block.children[0].category == 'unit'

        imported_unit_block = self.store.get_item(sourced_block.children[0])
        assert len(imported_unit_block.children) == 1
        assert imported_unit_block.children[0].category == 'html'

        imported_html_block = self.store.get_item(imported_unit_block.children[0])
        assert 'Hello world' in imported_html_block.data

        # Check that assets were imported and static paths were modified after importing
        assets = library_api.get_library_block_static_asset_files(html_block.scope_ids.usage_id)
        assert len(assets) == 1
        assert assets[0].url in imported_html_block.data

        # Check that reimporting updates the target block
        self._set_library_block_olx(html_block_id, '<html><a href="/static/test.txt">Foo bar</a></html>')
        self.tools.import_from_blockstore(sourced_block, [unit_block_id])

        assert len(sourced_block.children) == 1
        imported_unit_block = self.store.get_item(sourced_block.children[0])
        assert len(imported_unit_block.children) == 1
        imported_html_block = self.store.get_item(imported_unit_block.children[0])
        assert 'Hello world' not in imported_html_block.data
        assert 'Foo bar' in imported_html_block.data
