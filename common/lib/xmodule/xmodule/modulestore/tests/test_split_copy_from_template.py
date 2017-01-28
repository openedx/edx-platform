"""
Tests for split's copy_from_template method.
Currently it is only used for content libraries.
However for these tests, we make sure it also works when copying from course to course.
"""
import ddt
from shutil import rmtree
from tempfile import mkdtemp
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.exceptions import ItemNotFoundError
from xmodule.modulestore.tests.factories import CourseFactory, LibraryFactory
from xmodule.modulestore.tests.utils import MongoContentstoreBuilder, MixedSplitTestCase
from xmodule.modulestore.xml_importer import import_course_from_xml
from xmodule.modulestore.xml_exporter import export_course_to_xml


@ddt.ddt
class TestSplitCopyTemplate(MixedSplitTestCase):
    """
    Test for split's copy_from_template method.
    """

    def setUp(self):
        """
        Prepare environment for testing
        """
        super(TestSplitCopyTemplate, self).setUp()
        self.export_dir = mkdtemp()
        self.addCleanup(rmtree, self.export_dir, ignore_errors=True)

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
        vertical_block = self.make_block("vertical", source_container)
        problem_library_display_name = "Problem Library Display Name"
        problem_block = self.make_block(
            "problem", vertical_block, display_name=problem_library_display_name, markdown="Problem markdown here"
        )

        if source_type == LibraryFactory:
            source_container = self.store.get_library(
                source_container.location.library_key, remove_version=False, remove_branch=False
            )
        else:
            source_container = self.store.get_course(
                source_container.location.course_key, remove_version=False, remove_branch=False
            )

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

        # Check that when capa modules are copied, their "markdown" fields (Scope.settings) are removed.
        # (See note in split.py:copy_from_template())
        self.assertIsNotNone(problem_block.markdown)
        self.assertIsNone(problem_block_course.markdown)

        # Override the display_name and weight:
        new_display_name = "The Trouble with Tribbles"
        new_weight = 20
        problem_block_course.display_name = new_display_name
        problem_block_course.weight = new_weight
        self.store.update_item(problem_block_course, self.user_id)

        # Test that "Any previously existing children of `dest_usage`
        # that haven't been replaced/updated by this copy_from_template operation will be deleted."
        extra_block = self.make_block("html", vertical_block_course)

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

    def test_copy_from_template_publish(self):
        """
        Test that copy_from_template's "defaults" data is not lost
        when blocks are published.
        """
        # Create a library with a problem:
        source_library = LibraryFactory.create(modulestore=self.store)
        display_name_expected = "CUSTOM Library Display Name"
        self.make_block("problem", source_library, display_name=display_name_expected)
        # Reload source_library since we need its branch and version to use copy_from_template:
        source_library = self.store.get_library(
            source_library.location.library_key, remove_version=False, remove_branch=False
        )
        # And a course with a vertical:
        course = CourseFactory.create(modulestore=self.store)
        self.make_block("vertical", course)

        problem_key_in_course = self.store.copy_from_template(
            source_library.children, dest_key=course.location, user_id=self.user_id
        )[0]

        # We do the following twice because different methods get used inside
        # split modulestore on first vs. subsequent publish
        for __ in range(2):
            # Publish:
            self.store.publish(problem_key_in_course, self.user_id)
            # Test that the defaults values are there.
            problem_published = self.store.get_item(
                problem_key_in_course.for_branch(ModuleStoreEnum.BranchName.published)
            )
            self.assertEqual(problem_published.display_name, display_name_expected)

    def test_copy_from_template_auto_publish(self):
        """
        Make sure that copy_from_template works with things like 'chapter' that
        are always auto-published.
        """
        source_course = CourseFactory.create(modulestore=self.store)
        course = CourseFactory.create(modulestore=self.store)

        # Populate the course:
        about = self.make_block("about", source_course)
        chapter = self.make_block("chapter", source_course)
        sequential = self.make_block("sequential", chapter)
        # And three blocks that are NOT auto-published:
        vertical = self.make_block("vertical", sequential)
        self.make_block("problem", vertical)
        html = self.make_block("html", source_course)

        # Reload source_course since we need its branch and version to use copy_from_template:
        source_course = self.store.get_course(
            source_course.location.course_key, remove_version=False, remove_branch=False
        )

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
        # We can't use has_changes because it includes descendants
        self.assertTrue(published_version_exists(new_blocks["chapter"]))
        self.assertTrue(published_version_exists(new_blocks["sequential"]))  # Ditto
        # Check that non-auto-publish blocks and blocks with non-auto-publish descendants show changes:
        self.assertTrue(self.store.has_changes(new_blocks["html"]))
        self.assertTrue(self.store.has_changes(new_blocks["problem"]))
        # Will have changes since a child block has changes.
        self.assertTrue(self.store.has_changes(new_blocks["chapter"]))
        # Verify that our published_version_exists works
        self.assertFalse(published_version_exists(new_blocks["vertical"]))

    def test_copy_from_template_with_import_export(self):
        """
        Test that the behavior of import/export works correct after some block was copied with copy_from_template()
        """
        chapter_display_name = 'Test Chapter'
        sequential_display_name = 'Test Sequential'
        chapter_dst_display_name = 'Some New Chapter'

        # Create original course:
        course_original = CourseFactory.create(modulestore=self.store)
        chapter = self.make_block("chapter", course_original, display_name=chapter_display_name)
        sequential = self.make_block("sequential", chapter, display_name=sequential_display_name)

        # Create course where to copy sequential block
        course_dst = CourseFactory.create(modulestore=self.store)
        chapter_dst = self.make_block("chapter", course_dst, display_name=chapter_dst_display_name)

        new_blocks = self.store.copy_from_template([sequential.location], dest_key=chapter_dst.location,
                                                   user_id=self.user_id)
        self.store.publish(new_blocks[0], self.user_id)

        course_dst = self.store.get_course(course_dst.location.course_key)  # Reload from modulestore

        chapter_after_copy = self.store.get_item(course_dst.get_children()[0].location)
        self.assertEqual(chapter_after_copy.display_name, chapter_dst_display_name)

        sequential_after_copy = chapter_after_copy.get_children()[0]
        self.assertEqual(sequential_after_copy.display_name, sequential_display_name)

        course_dst_after_import_key = self.store.make_course_key('edX', "course_new", "2017_Fall_2")

        with MongoContentstoreBuilder().build() as contentstore:
            # export course to xml
            top_level_export_dir = 'exported_source_course'

            export_course_to_xml(
                self.store,
                contentstore,
                course_dst.id,
                self.export_dir,
                top_level_export_dir,
            )

            course_dst_after_import = import_course_from_xml(
                self.store,
                self.user_id,
                self.export_dir,
                source_dirs=[top_level_export_dir],
                static_content_store=contentstore,
                target_id=course_dst_after_import_key,
                create_if_not_present=True,
                raise_on_failure=True
            )

            chapter_after_import_location = course_dst_after_import[0].get_children()[0].location
            chapter_after_import = self.store.get_item(chapter_after_import_location)
            self.assertEqual(chapter_after_import.display_name, chapter_dst_display_name)

            sequential_after_import = chapter_after_import.get_children()[0]
            self.assertEqual(sequential_after_import.display_name, sequential_display_name)
