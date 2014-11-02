"""
Content library unit tests that require the CMS runtime.
"""
from contentstore.tests.utils import AjaxEnabledTestClient, parse_json
from contentstore.utils import reverse_usage_url
from contentstore.views.preview import _load_preview_module
from contentstore.views.tests.test_library import LIBRARY_REST_URL
import ddt
from xmodule.library_content_module import LibraryVersionReference
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.tests import get_test_system
from mock import Mock
from opaque_keys.edx.locator import CourseKey, LibraryLocator


@ddt.ddt
class TestLibraries(ModuleStoreTestCase):
    """
    High-level tests for libraries
    """
    def setUp(self):
        user_password = super(TestLibraries, self).setUp()

        self.client = AjaxEnabledTestClient()
        self.client.login(username=self.user.username, password=user_password)

        self.lib_key = self._create_library()
        self.library = modulestore().get_library(self.lib_key)

    def _create_library(self, org="org", library="lib", display_name="Test Library"):
        """
        Helper method used to create a library. Uses the REST API.
        """
        response = self.client.ajax_post(LIBRARY_REST_URL, {
            'org': org,
            'library': library,
            'display_name': display_name,
        })
        self.assertEqual(response.status_code, 200)
        lib_info = parse_json(response)
        lib_key = CourseKey.from_string(lib_info['library_key'])
        self.assertIsInstance(lib_key, LibraryLocator)
        return lib_key

    def _add_library_content_block(self, course, library_key, other_settings=None):
        """
        Helper method to add a LibraryContent block to a course.
        The block will be configured to select content from the library
        specified by library_key.
        other_settings can be a dict of Scope.settings fields to set on the block.
        """
        return ItemFactory.create(
            category='library_content',
            parent_location=course.location,
            user_id=self.user.id,
            publish_item=False,
            source_libraries=[LibraryVersionReference(library_key)],
            **(other_settings or {})
        )

    def _refresh_children(self, lib_content_block):
        """
        Helper method: Uses the REST API to call the 'refresh_children' handler
        of a LibraryContent block
        """
        if 'user' not in lib_content_block.runtime._services:  # pylint: disable=protected-access
            lib_content_block.runtime._services['user'] = Mock(user_id=self.user.id)  # pylint: disable=protected-access
        handler_url = reverse_usage_url('component_handler', lib_content_block.location, kwargs={'handler': 'refresh_children'})
        response = self.client.ajax_post(handler_url)
        self.assertEqual(response.status_code, 200)
        return modulestore().get_item(lib_content_block.location)

    @ddt.data(
        (2, 1, 1),
        (2, 2, 2),
        (2, 20, 2),
    )
    @ddt.unpack
    def test_max_items(self, num_to_create, num_to_select, num_expected):
        """
        Test the 'max_count' property of LibraryContent blocks.
        """
        for _ in range(0, num_to_create):
            ItemFactory.create(category="html", parent_location=self.library.location, user_id=self.user.id, publish_item=False)

        with modulestore().default_store(ModuleStoreEnum.Type.split):
            course = CourseFactory.create()

        lc_block = self._add_library_content_block(course, self.lib_key, {'max_count': num_to_select})
        self.assertEqual(len(lc_block.children), 0)
        lc_block = self._refresh_children(lc_block)

        # Now, we want to make sure that .children has the total # of potential
        # children, and that get_child_descriptors() returns the actual children
        # chosen for a given student.
        # In order to be able to call get_child_descriptors(), we must first
        # call bind_for_student:
        lc_block.bind_for_student(get_test_system(), lc_block._field_data)  # pylint: disable=protected-access
        self.assertEqual(len(lc_block.children), num_to_create)
        self.assertEqual(len(lc_block.get_child_descriptors()), num_expected)

    def test_consistent_children(self):
        """
        Test that the same student will always see the same selected child block
        """
        session_data = {}

        def bind_module(descriptor):
            """
            Helper to use the CMS's module system so we can access student-specific fields.
            """
            request = Mock(user=self.user, session=session_data)
            return _load_preview_module(request, descriptor)  # pylint: disable=protected-access

        # Create many blocks in the library and add them to a course:
        for num in range(0, 8):
            ItemFactory.create(
                data="This is #{}".format(num + 1),
                category="html", parent_location=self.library.location, user_id=self.user.id, publish_item=False
            )

        with modulestore().default_store(ModuleStoreEnum.Type.split):
            course = CourseFactory.create()

        lc_block = self._add_library_content_block(course, self.lib_key, {'max_count': 1})
        lc_block_key = lc_block.location
        lc_block = self._refresh_children(lc_block)

        def get_child_of_lc_block(block):
            """
            Fetch the child shown to the current user.
            """
            children = block.get_child_descriptors()
            self.assertEqual(len(children), 1)
            return children[0]

        # Check which child a student will see:
        bind_module(lc_block)
        chosen_child = get_child_of_lc_block(lc_block)
        chosen_child_defn_id = chosen_child.definition_locator.definition_id
        lc_block.save()

        modulestore().update_item(lc_block, self.user.id)

        # Now re-load the block and try again:
        def check():
            """
            Confirm that chosen_child is still the child seen by the test student
            """
            for _ in range(0, 6):  # Repeat many times b/c blocks are randomized
                lc_block = modulestore().get_item(lc_block_key)  # Reload block from the database
                bind_module(lc_block)
                current_child = get_child_of_lc_block(lc_block)
                self.assertEqual(current_child.location, chosen_child.location)
                self.assertEqual(current_child.data, chosen_child.data)
                self.assertEqual(current_child.definition_locator.definition_id, chosen_child_defn_id)

        check()
        # Refresh the children:
        lc_block = self._refresh_children(lc_block)
        # Now re-load the block and try yet again, in case refreshing the children changed anything:
        check()

    def test_definition_shared_with_library(self):
        """
        Test that the same block definition is used for the library and course[s]
        """
        block1 = ItemFactory.create(category="html", parent_location=self.library.location, user_id=self.user.id, publish_item=False)
        def_id1 = block1.definition_locator.definition_id
        block2 = ItemFactory.create(category="html", parent_location=self.library.location, user_id=self.user.id, publish_item=False)
        def_id2 = block2.definition_locator.definition_id
        self.assertNotEqual(def_id1, def_id2)

        # Next, create a course:
        with modulestore().default_store(ModuleStoreEnum.Type.split):
            course = CourseFactory.create()

        # Add a LibraryContent block to the course:
        lc_block = self._add_library_content_block(course, self.lib_key)
        lc_block = self._refresh_children(lc_block)
        for child_key in lc_block.children:
            child = modulestore().get_item(child_key)
            def_id = child.definition_locator.definition_id
            self.assertIn(def_id, (def_id1, def_id2))

    def test_fields(self):
        """
        Test that blocks used from a library have the same field values as
        defined by the library author.
        """
        data_value = "A Scope.content value"
        name_value = "A Scope.settings value"
        lib_block = ItemFactory.create(
            category="html",
            parent_location=self.library.location,
            user_id=self.user.id,
            publish_item=False,
            display_name=name_value,
            data=data_value,
        )
        self.assertEqual(lib_block.data, data_value)
        self.assertEqual(lib_block.display_name, name_value)

        # Next, create a course:
        with modulestore().default_store(ModuleStoreEnum.Type.split):
            course = CourseFactory.create()

        # Add a LibraryContent block to the course:
        lc_block = self._add_library_content_block(course, self.lib_key)
        lc_block = self._refresh_children(lc_block)
        course_block = modulestore().get_item(lc_block.children[0])

        self.assertEqual(course_block.data, data_value)
        self.assertEqual(course_block.display_name, name_value)

    def test_block_with_children(self):
        """
        Test that blocks used from a library can have children.
        """
        data_value = "A Scope.content value"
        name_value = "A Scope.settings value"
        # In the library, create a vertical block with a child:
        vert_block = ItemFactory.create(
            category="vertical",
            parent_location=self.library.location,
            user_id=self.user.id,
            publish_item=False,
        )
        child_block = ItemFactory.create(
            category="html",
            parent_location=vert_block.location,
            user_id=self.user.id,
            publish_item=False,
            display_name=name_value,
            data=data_value,
        )
        self.assertEqual(child_block.data, data_value)
        self.assertEqual(child_block.display_name, name_value)

        # Next, create a course:
        with modulestore().default_store(ModuleStoreEnum.Type.split):
            course = CourseFactory.create()

        # Add a LibraryContent block to the course:
        lc_block = self._add_library_content_block(course, self.lib_key)
        lc_block = self._refresh_children(lc_block)
        self.assertEqual(len(lc_block.children), 1)
        course_vert_block = modulestore().get_item(lc_block.children[0])
        self.assertEqual(len(course_vert_block.children), 1)
        course_child_block = modulestore().get_item(course_vert_block.children[0])

        self.assertEqual(course_child_block.data, data_value)
        self.assertEqual(course_child_block.display_name, name_value)
