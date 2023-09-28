"""
Tests for split's copy_from_template method.
Currently it is only used for content libraries.
However for these tests, we make sure it also works when copying from course to course.
"""


import ddt
import pytest

from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.exceptions import ItemNotFoundError
from xmodule.modulestore.tests.factories import CourseFactory, LibraryFactory
from xmodule.modulestore.tests.utils import MixedSplitTestCase


@ddt.ddt
class TestSplitCopyTemplate(MixedSplitTestCase):
    """
    Test for split's copy_from_template method.
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
        assert len(new_blocks) == 1

        course = self.store.get_course(course.location.course_key)  # Reload from modulestore

        assert len(course.children) == 1
        vertical_block_course = self.store.get_item(course.children[0])
        assert new_blocks[0] == vertical_block_course.location
        problem_block_course = self.store.get_item(vertical_block_course.children[0])
        assert problem_block_course.display_name == problem_library_display_name

        # Check that when capa blocks are copied, their "markdown" fields (Scope.settings) are removed.
        # (See note in split.py:copy_from_template())
        assert problem_block.markdown is not None
        assert problem_block_course.markdown is None

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
        assert new_blocks == new_blocks2
        # Reload problem_block_course:
        problem_block_course = self.store.get_item(problem_block_course.location)
        assert problem_block_course.display_name == new_display_name
        assert problem_block_course.weight == new_weight

        # Ensure that extra_block was deleted:
        vertical_block_course = self.store.get_item(new_blocks2[0])
        assert len(vertical_block_course.children) == 1
        with pytest.raises(ItemNotFoundError):
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
            assert problem_published.display_name == display_name_expected

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
        assert len(block_keys) == len(source_keys)

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
        assert not self.store.has_changes(new_blocks['about'])
        # We can't use has_changes because it includes descendants
        assert published_version_exists(new_blocks['chapter'])
        assert published_version_exists(new_blocks['sequential'])
        # Ditto
        # Check that non-auto-publish blocks and blocks with non-auto-publish descendants show changes:
        assert self.store.has_changes(new_blocks['html'])
        assert self.store.has_changes(new_blocks['problem'])
        # Will have changes since a child block has changes.
        assert self.store.has_changes(new_blocks['chapter'])
        # Verify that our published_version_exists works
        assert not published_version_exists(new_blocks['vertical'])
