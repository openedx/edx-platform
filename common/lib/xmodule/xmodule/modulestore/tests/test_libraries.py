# -*- coding: utf-8 -*-
"""
Basic unit tests related to content libraries.

Higher-level tests are in `cms/djangoapps/contentstore`.
"""


import ddt
import six
from bson.objectid import ObjectId
from opaque_keys.edx.locator import LibraryLocator
from six.moves import range

from xmodule.modulestore.exceptions import DuplicateCourseError
from xmodule.modulestore.tests.factories import ItemFactory, LibraryFactory, check_mongo_calls
from xmodule.modulestore.tests.utils import MixedSplitTestCase


@ddt.ddt
class TestLibraries(MixedSplitTestCase):
    """
    Test for libraries.
    Mostly tests code found throughout split mongo, but also tests library_root_xblock.py
    """

    def test_create_library(self):
        """
        Test that we can create a library, and see how many mongo calls it uses to do so.

        Expected mongo calls, in order:
        find_one({'org': '...', 'run': 'library', 'course': '...'})
        insert(definition: {'block_type': 'library', 'fields': {}})

        insert_structure(bulk)
        insert_course_index(bulk)
        get_course_index(bulk)
        """
        with check_mongo_calls(2, 3):
            LibraryFactory.create(modulestore=self.store)

    def test_duplicate_library(self):
        """
        Make sure we cannot create duplicate libraries
        """
        org, lib_code = ('DuplicateX', "DUP")
        LibraryFactory.create(org=org, library=lib_code, modulestore=self.store)
        with self.assertRaises(DuplicateCourseError):
            LibraryFactory.create(org=org, library=lib_code, modulestore=self.store)

    @ddt.data(
        "This is a test library!",
        u"Ωμέγα Βιβλιοθήκη",
    )
    def test_str_repr(self, name):
        """
        Test __unicode__() and __str__() methods of libraries
        """
        library = LibraryFactory.create(metadata={"display_name": name}, modulestore=self.store)
        self.assertIn(name, six.text_type(library))
        if not isinstance(name, six.text_type):
            self.assertIn(name, str(library))

    def test_display_with_default_methods(self):
        """
        Check that the display_x_with_default methods have been implemented, for
        compatibility with courses.
        """
        org = 'TestOrgX'
        lib_code = 'LC101'
        library = LibraryFactory.create(org=org, library=lib_code, modulestore=self.store)
        self.assertEqual(library.display_org_with_default, org)
        self.assertEqual(library.display_number_with_default, lib_code)

    def test_block_with_children(self):
        """
        Test that blocks used from a library can have children.
        """
        library = LibraryFactory.create(modulestore=self.store)

        # In the library, create a vertical block with a child:
        vert_block = ItemFactory.create(
            category="vertical",
            parent_location=library.location,
            user_id=self.user_id,
            publish_item=False,
            modulestore=self.store,
        )
        child_block = ItemFactory.create(
            category="html",
            parent_location=vert_block.location,
            user_id=self.user_id,
            publish_item=False,
            metadata={"data": "Hello world", },
            modulestore=self.store,
        )
        self.assertEqual(child_block.parent.replace(version_guid=None, branch=None), vert_block.location)

    def test_update_item(self):
        """
        Test that update_item works for a block in a library
        """
        library = LibraryFactory.create(modulestore=self.store)

        block = ItemFactory.create(
            category="html",
            parent_location=library.location,
            user_id=self.user_id,
            publish_item=False,
            metadata={"data": "Hello world", },
            modulestore=self.store,
        )
        block_key = block.location
        block.data = "NEW"
        old_version = self.store.get_item(block_key, remove_version=False, remove_branch=False).location.version_guid
        self.store.update_item(block, self.user_id)
        # Reload block from the modulestore
        block = self.store.get_item(block_key)
        self.assertEqual(block.data, "NEW")
        self.assertEqual(block.location, block_key)
        new_version = self.store.get_item(block_key, remove_version=False, remove_branch=False).location.version_guid
        self.assertNotEqual(old_version, new_version)

    def test_delete_item(self):
        """
        Test to make sure delete_item() works on blocks in a library
        """
        library = LibraryFactory.create(modulestore=self.store)
        lib_key = library.location.library_key
        block = ItemFactory.create(
            category="html",
            parent_location=library.location,
            user_id=self.user_id,
            publish_item=False,
            modulestore=self.store,
        )
        library = self.store.get_library(lib_key)
        self.assertEqual(len(library.children), 1)
        self.store.delete_item(block.location, self.user_id)
        library = self.store.get_library(lib_key)
        self.assertEqual(len(library.children), 0)

    def test_get_library_non_existent(self):
        """ Test get_library() with non-existent key """
        result = self.store.get_library(LibraryLocator("non", "existent"))
        self.assertEqual(result, None)

    def test_get_libraries(self):
        """ Test get_libraries() """
        libraries = [LibraryFactory.create(modulestore=self.store) for _ in range(3)]
        lib_dict = dict([(lib.location.library_key, lib) for lib in libraries])

        lib_list = self.store.get_libraries()

        self.assertEqual(len(lib_list), len(libraries))
        for lib in lib_list:
            self.assertIn(lib.location.library_key, lib_dict)

    def test_strip(self):
        """
        Test that library keys coming out of MixedModuleStore are stripped of
        branch and version info by default.
        """
        # Create a library
        lib_key = LibraryFactory.create(modulestore=self.store).location.library_key
        # Re-load the library from the modulestore, explicitly including version information:
        lib = self.store.get_library(lib_key)
        self.assertEqual(lib.location.version_guid, None)
        self.assertEqual(lib.location.branch, None)
        self.assertEqual(lib.location.library_key.version_guid, None)
        self.assertEqual(lib.location.library_key.branch, None)

    def test_get_lib_version(self):
        """
        Test that we can get version data about a library from get_library()
        """
        # Create a library
        lib_key = LibraryFactory.create(modulestore=self.store).location.library_key
        # Re-load the library from the modulestore, explicitly including version information:
        lib = self.store.get_library(lib_key, remove_version=False, remove_branch=False)
        version = lib.location.library_key.version_guid
        self.assertIsInstance(version, ObjectId)

    def test_xblock_in_lib_have_published_version_returns_false(self):
        library = LibraryFactory.create(modulestore=self.store)
        block = ItemFactory.create(
            category="html",
            parent_location=library.location,
            user_id=self.user_id,
            publish_item=False,
            modulestore=self.store,
        )
        self.assertFalse(self.store.has_published_version(block))
