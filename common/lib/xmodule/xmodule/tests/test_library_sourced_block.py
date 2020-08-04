"""
Tests for Source from Library XBlock
"""
from xblockutils.resources import ResourceLoader

from openedx.core.djangoapps.content_libraries.tests.base import ContentLibrariesRestApiTest
from student.roles import CourseInstructorRole
from cms.lib.xblock.runtime import handler_url
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.tests import get_test_system
from xmodule.x_module import AUTHOR_VIEW, STUDENT_VIEW


class LibrarySourcedBlockTestCase(ContentLibrariesRestApiTest):
    """
    Tests for LibraryToolsService which interact with blockstore-based content libraries
    """
    def setUp(self):
        super().setUp()
        self.store = modulestore()

    def test_block_views(self):
        # Create a blockstore content library
        library = self._create_library(slug="testlib1_preview", title="Test Library 1", description="Testing XBlocks")
        # Add content to the library
        html_block_id = self._add_block_to_library(library["id"], "html", "html_student_preview")["id"]
        self._set_library_block_olx(html_block_id, '<html>Student Preview Test</html>')

        # Create a modulestore course
        course = CourseFactory.create(modulestore=self.store, user_id=self.user.id)
        CourseInstructorRole(course.id).add_users(self.user)
        # Add a "Source from Library" block to the course
        source_block = ItemFactory.create(
            category="library_sourced",
            parent=course,
            parent_location=course.location,
            user_id=self.user.id,
            modulestore=self.store
        )

        # Check if author_view for empty block renders using the editor template
        html = source_block.render(AUTHOR_VIEW).content
        loader = ResourceLoader('xmodule.library_sourced_block')
        expected_html = loader.render_django_template('templates/library-sourced-block-author-view.html', {
            'save_url': handler_url(source_block, 'submit_studio_edits')
        })
        self.assertEqual(expected_html, html)

        submit_studio_edits_url = '/xblock/{0}/handler/submit_studio_edits'.format(source_block.scope_ids.usage_id)
        post_data = {"values": {"source_block_id": html_block_id}, "defaults": ["display_name"]}
        # Import the html block from the library to the course
        self.client.post(submit_studio_edits_url, data=post_data, format='json')

        # Check if author_view for a configured block renders the children correctly
        # Use self.get_block_view for rendering these as mako templates are mocked to return repr of the template
        # instead of the rendered html
        res = self.get_block_view(source_block, AUTHOR_VIEW)
        self.assertNotIn('library-sourced-block-author-view.html', res)
        self.assertIn('studio_render_children_view.html', res)
        self.assertIn('Student Preview Test', res)

        # Check if student_view renders the children correctly
        res = self.get_block_view(source_block, STUDENT_VIEW)
        self.assertIn('Student Preview Test', res)

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
