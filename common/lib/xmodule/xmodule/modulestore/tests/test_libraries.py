# -*- coding: utf-8 -*-
"""
Basic unit tests related to content libraries.

Higher-level tests are in `cms/djangoapps/contentstore`.
"""
from bson.objectid import ObjectId
import ddt
from mock import patch
from opaque_keys.edx.locator import LibraryLocator
from xblock.fragment import Fragment
from xblock.runtime import Runtime as VanillaRuntime
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.exceptions import DuplicateCourseError, ItemNotFoundError
from xmodule.modulestore.tests.factories import CourseFactory, LibraryFactory, ItemFactory, check_mongo_calls
from xmodule.modulestore.tests.utils import MixedSplitTestCase
from xmodule.x_module import AUTHOR_VIEW


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
        self.assertIn(name, unicode(library))
        if not isinstance(name, unicode):
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
        libraries = [LibraryFactory.create(modulestore=self.store) for _ in range(0, 3)]
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

    @patch('xmodule.modulestore.split_mongo.caching_descriptor_system.CachingDescriptorSystem.render', VanillaRuntime.render)
    def test_library_author_view(self):
        """
        Test that LibraryRoot.author_view can run and includes content from its
        children.
        We have to patch the runtime (module system) in order to be able to
        render blocks in our test environment.
        """
        library = LibraryFactory.create(modulestore=self.store)
        # Add one HTML block to the library:
        ItemFactory.create(
            category="html",
            parent_location=library.location,
            user_id=self.user_id,
            publish_item=False,
            modulestore=self.store,
        )
        library = self.store.get_library(library.location.library_key)

        context = {'reorderable_items': set(), }
        # Patch the HTML block to always render "Hello world"
        message = u"Hello world"
        hello_render = lambda _, context: Fragment(message)
        with patch('xmodule.html_module.HtmlDescriptor.author_view', hello_render, create=True):
            with patch('xmodule.x_module.DescriptorSystem.applicable_aside_types', lambda self, block: []):
                result = library.render(AUTHOR_VIEW, context)
        self.assertIn(message, result.content)

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


@ddt.ddt
class TestSplitCopyTemplate(MixedSplitTestCase):
    """
    Test for split's copy_from_template method.
    Currently it is only used for content libraries.
    However for this test, we make sure it also works when copying from course to course.
    """
    @ddt.data(
        LibraryFactory,
        CourseFactory,
    )
    def test_copy_from_template(self, source_type):
        """
        Test that the behavior of copy_from_template() matches its docstring
        """
        source_container = source_type.create(modulestore=self.store)  # Either a library or a course
        course = CourseFactory.create(modulestore=self.store)
        # Add a vertical with a capa child to the source library/course:
        vertical_block = ItemFactory.create(
            category="vertical",
            parent_location=source_container.location,
            user_id=self.user_id,
            publish_item=False,
            modulestore=self.store,
        )
        problem_library_display_name = "Problem Library Display Name"
        problem_block = ItemFactory.create(
            category="problem",
            parent_location=vertical_block.location,
            user_id=self.user_id,
            publish_item=False,
            modulestore=self.store,
            display_name=problem_library_display_name,
            markdown="Problem markdown here"
        )

        if source_type == LibraryFactory:
            source_container = self.store.get_library(source_container.location.library_key, remove_version=False, remove_branch=False)
        else:
            source_container = self.store.get_course(source_container.location.course_key, remove_version=False, remove_branch=False)

        # Inherit the vertical and the problem from the library into the course:
        source_keys = [source_container.children[0]]
        new_blocks = self.store.copy_from_template(source_keys, dest_key=course.location, user_id=self.user_id)
        self.assertEqual(len(new_blocks), 1)

        course = self.store.get_course(course.location.course_key)  # Reload from modulestore

        self.assertEqual(len(course.children), 1)
        vertical_block_course = self.store.get_item(course.children[0])
        self.assertEqual(new_blocks[0], vertical_block_course.location)
        problem_block_course = self.store.get_item(vertical_block_course.children[0])
        self.assertEqual(problem_block_course.display_name, problem_library_display_name)

        # Check that when capa modules are copied, their "markdown" fields (Scope.settings) are removed. (See note in split.py:copy_from_template())
        self.assertIsNotNone(problem_block.markdown)
        self.assertIsNone(problem_block_course.markdown)

        # Override the display_name and weight:
        new_display_name = "The Trouble with Tribbles"
        new_weight = 20
        problem_block_course.display_name = new_display_name
        problem_block_course.weight = new_weight
        self.store.update_item(problem_block_course, self.user_id)

        # Test that "Any previously existing children of `dest_usage` that haven't been replaced/updated by this copy_from_template operation will be deleted."
        extra_block = ItemFactory.create(
            category="html",
            parent_location=vertical_block_course.location,
            user_id=self.user_id,
            publish_item=False,
            modulestore=self.store,
        )

        # Repeat the copy_from_template():
        new_blocks2 = self.store.copy_from_template(source_keys, dest_key=course.location, user_id=self.user_id)
        self.assertEqual(new_blocks, new_blocks2)
        # Reload problem_block_course:
        problem_block_course = self.store.get_item(problem_block_course.location)
        self.assertEqual(problem_block_course.display_name, new_display_name)
        self.assertEqual(problem_block_course.weight, new_weight)

        # Ensure that extra_block was deleted:
        vertical_block_course = self.store.get_item(new_blocks2[0])
        self.assertEqual(len(vertical_block_course.children), 1)
        with self.assertRaises(ItemNotFoundError):
            self.store.get_item(extra_block.location)

    def test_copy_from_template_auto_publish(self):
        """
        Make sure that copy_from_template works with things like 'chapter' that
        are always auto-published.
        """
        source_course = CourseFactory.create(modulestore=self.store)
        course = CourseFactory.create(modulestore=self.store)
        make_block = lambda category, parent: ItemFactory.create(category=category, parent_location=parent.location, user_id=self.user_id, modulestore=self.store)

        # Populate the course:
        about = make_block("about", source_course)
        chapter = make_block("chapter", source_course)
        sequential = make_block("sequential", chapter)
        # And three blocks that are NOT auto-published:
        vertical = make_block("vertical", sequential)
        make_block("problem", vertical)
        html = make_block("html", source_course)

        # Reload source_course since we need its branch and version to use copy_from_template:
        source_course = self.store.get_course(source_course.location.course_key, remove_version=False, remove_branch=False)

        # Inherit the vertical and the problem from the library into the course:
        source_keys = [block.location for block in [about, chapter, html]]
        block_keys = self.store.copy_from_template(source_keys, dest_key=course.location, user_id=self.user_id)
        self.assertEqual(len(block_keys), len(source_keys))

        # Build dict of the new blocks in 'course', keyed by category (which is a unique key in our case)
        new_blocks = {}
        block_keys = set(block_keys)
        while block_keys:
            key = block_keys.pop()
            block = self.store.get_item(key)
            new_blocks[block.category] = block
            block_keys.update(set(getattr(block, "children", [])))

        # Check that auto-publish blocks with no children are indeed published:
        def published_version_exists(block):
            """ Does a published version of block exist? """
            try:
                self.store.get_item(block.location.for_branch(ModuleStoreEnum.BranchName.published))
                return True
            except ItemNotFoundError:
                return False

        # Check that the auto-publish blocks have been published:
        self.assertFalse(self.store.has_changes(new_blocks["about"]))
        self.assertTrue(published_version_exists(new_blocks["chapter"]))  # We can't use has_changes because it includes descendants
        self.assertTrue(published_version_exists(new_blocks["sequential"]))  # Ditto
        # Check that non-auto-publish blocks and blocks with non-auto-publish descendants show changes:
        self.assertTrue(self.store.has_changes(new_blocks["html"]))
        self.assertTrue(self.store.has_changes(new_blocks["problem"]))
        self.assertTrue(self.store.has_changes(new_blocks["chapter"]))  # Will have changes since a child block has changes.
        self.assertFalse(published_version_exists(new_blocks["vertical"]))  # Verify that our published_version_exists works
