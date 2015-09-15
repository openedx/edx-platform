"""
Tests for the fix_not_found management command
"""

from django.core.management import call_command
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.split_mongo import BlockKey


class TestFixNotFound(ModuleStoreTestCase):
    """
    Tests for the fix_not_found management command
    """
    def test_fix_not_found_non_split(self):
        course = CourseFactory(default_store=ModuleStoreEnum.Type.mongo)
        with self.assertRaises(SystemExit):
            call_command("fix_not_found", unicode(course.id))

    def test_fix_not_found(self):
        course = CourseFactory(default_store=ModuleStoreEnum.Type.split)
        # pylint: disable=protected-access
        store = self.store._get_modulestore_for_courselike(course.id)
        course_locator = course.id.for_branch(ModuleStoreEnum.BranchName.draft)
        ItemFactory.create(category='sequential', parent_location=course.location)

        # create a dangling usage key that we'll add to the course structure
        dangling_pointer = course_locator.make_usage_key('sequential', 'ImNotThere')

        # pylint: disable=protected-access
        original_structure = store._lookup_course(course_locator).structure
        index_entry = store._get_index_if_valid(course_locator)
        new_structure = store.version_structure(
            course_locator, original_structure, ModuleStoreEnum.UserID.mgmt_command
        )

        # add the empty pointer as a child of `course`
        course_block_key = BlockKey.from_usage_key(course.location)
        course_children = new_structure['blocks'][course_block_key].fields['children']

        # update the course_structure
        new_structure['blocks'][course_block_key].fields['children'].append(
            BlockKey.from_usage_key(dangling_pointer)
        )
        store.update_structure(course_locator, new_structure)
        # pylint: disable=protected-access
        store._update_head(course_locator, index_entry, course_locator.branch, new_structure['_id'])

        # make sure both the real and dangling pointers are children of course
        # pylint: disable=protected-access
        structure = store._lookup_course(course_locator).structure
        course_children = structure['blocks'][course_block_key].fields['children']
        self.assertEqual(len(course_children), 2)
        self.assertIn(BlockKey.from_usage_key(dangling_pointer), course_children)

        call_command("fix_not_found", unicode(course.id))

        # make sure the dangling pointer was removed from the course's children
        # pylint: disable=protected-access
        structure = store._lookup_course(course_locator).structure
        course_children = structure['blocks'][course_block_key].fields['children']
        self.assertEqual(len(course_children), 1)
        self.assertNotIn(BlockKey.from_usage_key(dangling_pointer), course_children)
