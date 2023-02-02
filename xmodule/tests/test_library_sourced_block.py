"""
Tests for Source from Library XBlock
"""

from openedx.core.djangoapps.content_libraries.tests.base import ContentLibrariesRestApiTest
from common.djangoapps.student.roles import CourseInstructorRole
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.factories import CourseFactory, BlockFactory
from xmodule.tests import get_test_system
from xmodule.x_module import STUDENT_VIEW  # lint-amnesty, pylint: disable=unused-import


class LibrarySourcedBlockTestCase(ContentLibrariesRestApiTest):
    """
    Tests for LibraryToolsService which interact with blockstore-based content libraries
    """
    def setUp(self):
        super().setUp()
        self.store = modulestore()
        # Create a modulestore course
        course = CourseFactory.create(modulestore=self.store, user_id=self.user.id)
        CourseInstructorRole(course.id).add_users(self.user)
        # Add a "Source from Library" block to the course
        self.source_block = BlockFactory.create(
            category="library_sourced",
            parent=course,
            parent_location=course.location,
            user_id=self.user.id,
            modulestore=self.store
        )
        self.submit_url = f'/xblock/{self.source_block.scope_ids.usage_id}/handler/submit_studio_edits'

    def test_block_views(self):
        # Create a blockstore content library
        library = self._create_library(slug="testlib1_preview", title="Test Library 1", description="Testing XBlocks")
        # Add content to the library
        html_block_1 = self._add_block_to_library(library["id"], "html", "html_student_preview_1")["id"]
        self._set_library_block_olx(html_block_1, '<html>Student Preview Test 1</html>')
        html_block_2 = self._add_block_to_library(library["id"], "html", "html_student_preview_2")["id"]
        self._set_library_block_olx(html_block_2, '<html>Student Preview Test 2</html>')

        # Import the html blocks from the library to the course
        post_data = {"values": {"source_block_ids": [html_block_1, html_block_2]}, "defaults": ["display_name"]}
        res = self.client.post(self.submit_url, data=post_data, format='json')

        # Check if student_view renders the children correctly
        res = self.get_block_view(self.source_block, STUDENT_VIEW)
        assert 'Student Preview Test 1' in res
        assert 'Student Preview Test 2' in res

    def test_block_limits(self):
        # Create a blockstore content library
        library = self._create_library(slug="testlib2_preview", title="Test Library 2", description="Testing XBlocks")
        # Add content to the library
        blocks = [self._add_block_to_library(library["id"], "html", f"block_{i}")["id"] for i in range(11)]

        # Import the html blocks from the library to the course
        post_data = {"values": {"source_block_ids": blocks}, "defaults": ["display_name"]}
        res = self.client.post(self.submit_url, data=post_data, format='json')
        assert res.status_code == 400
        assert res.json()['error']['messages'][0]['text'] == 'A maximum of 10 components may be added.'

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
