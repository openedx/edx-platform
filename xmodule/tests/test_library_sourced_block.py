"""
Tests for Source from Library XBlock
"""

from xmodule.library_tools import LibraryToolsService
from xmodule.modulestore.tests.factories import CourseFactory, LibraryFactory
from xmodule.modulestore.tests.utils import MixedSplitTestCase
from xmodule.tests import get_test_system
from xmodule.x_module import STUDENT_VIEW  # lint-amnesty, pylint: disable=unused-import

from openedx.core.djangoapps.content_libraries.tests.base import ContentLibrariesRestApiTest


class LibrarySourcedBlockTestCase(MixedSplitTestCase, ContentLibrariesRestApiTest):
    """
    Tests for LibraryToolsService which interact with blockstore-based content libraries
    """
    def setUp(self):
        super().setUp()
        self.tools = LibraryToolsService(self.store, self.user_id)
        self.library = LibraryFactory.create(modulestore=self.store)
        # Add content to the library
        self.lib_blocks = [
            self.make_block("html", self.library, data=f"Hello world from block {i}")
            for i in range(1, 5)
        ]
        # Create a modulestore course
        self.course = CourseFactory.create(modulestore=self.store)
        self.chapter = self.make_block("chapter", self.course)
        self.sequential = self.make_block("sequential", self.chapter)
        self.vertical = self.make_block("vertical", self.sequential)
        # Add a LibrarySourcedBlock to the course
        self.source_block = self.make_block(
            "library_sourced",
            self.vertical,
            source_library_id=str(self.library.location.library_key)
        )
        self.submit_url = f'/xblock/{self.source_block.scope_ids.usage_id}/handler/submit_studio_edits'

    def test_block_views(self):
        # Import the html blocks from the library to the course
        self.source_block.refresh_children()
        # Save children block_ids as source_block_ids
        source_block_ids = [str(child) for child in self.source_block.children]
        post_data = {"values": {"source_block_ids": source_block_ids}}
        res = self.client.post(self.submit_url, data=post_data, format='json')

        # Check if student_view renders the children correctly
        res = self.get_block_view(self.source_block, STUDENT_VIEW)
        for i in range(1, 5):
            assert f"Hello world from block {i}" in res

    def get_block_view(self, block, view, context=None):
        """
        Renders the specified view for a given XBlock
        """
        context = context or {}
        block = self.store.get_item(block.location)
        module_system = get_test_system(block)
        module_system.descriptor_runtime = block._runtime  # pylint: disable=protected-access
        block.bind_for_student(module_system, self.user.id)
        return module_system.render(block, view, context).content
