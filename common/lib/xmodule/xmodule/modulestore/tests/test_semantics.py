"""
Tests of modulestore semantics: How do the interfaces methods of ModuleStore relate to each other?
"""

import ddt
from collections import namedtuple

from xmodule.modulestore.tests.utils import (
    PureModulestoreTestCase, MongoModulestoreBuilder,
    SPLIT_MODULESTORE_SETUP
)
from xmodule.modulestore.exceptions import ItemNotFoundError
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.draft_and_published import DIRECT_ONLY_CATEGORIES
from xblock.core import XBlock

DETACHED_BLOCK_TYPES = dict(XBlock.load_tagged_classes('detached'))

# These tests won't work with courses, since they're creating blocks inside courses
TESTABLE_BLOCK_TYPES = set(DIRECT_ONLY_CATEGORIES)
TESTABLE_BLOCK_TYPES.discard('course')

TestField = namedtuple('TestField', ['field_name', 'initial', 'updated'])


@ddt.ddt
class DirectOnlyCategorySemantics(PureModulestoreTestCase):
    """
    Verify the behavior of Direct Only items
    blocks intended to store snippets of course content.
    """

    __test__ = False

    DATA_FIELDS = {
        'about': TestField('data', '<div>test data</div>', '<div>different test data</div>'),
        'chapter': TestField('is_entrance_exam', True, False),
        'sequential': TestField('is_entrance_exam', True, False),
        'static_tab': TestField('data', '<div>test data</div>', '<div>different test data</div>'),
        'course_info': TestField('data', '<div>test data</div>', '<div>different test data</div>'),
    }

    def setUp(self):
        super(DirectOnlyCategorySemantics, self).setUp()
        self.course = CourseFactory.create(
            org='test_org',
            number='999',
            run='test_run',
            display_name='My Test Course',
            modulestore=self.store
        )

    def assertBlockDoesntExist(self):
        with self.assertRaises(ItemNotFoundError):
            self.store.get_item(self.block_usage_key, revision=ModuleStoreEnum.RevisionOption.published_only)
        with self.assertRaises(ItemNotFoundError):
            self.store.get_item(self.block_usage_key, revision=ModuleStoreEnum.RevisionOption.draft_only)

        with self.store.branch_setting(ModuleStoreEnum.Branch.draft_preferred):
            with self.assertRaises(ItemNotFoundError):
                self.store.get_item(self.block_usage_key)

        with self.store.branch_setting(ModuleStoreEnum.Branch.published_only):
            with self.assertRaises(ItemNotFoundError):
                self.store.get_item(self.block_usage_key)

    def assertBlockHasContent(self, test_data, content):
        target_block = self.store.get_item(
            self.block_usage_key,
            revision=ModuleStoreEnum.RevisionOption.published_only
        )

        self.assertEquals(content, target_block.fields[test_data.field_name].read_from(target_block))

        target_block = self.store.get_item(
            self.block_usage_key,
            revision=ModuleStoreEnum.RevisionOption.draft_only
        )
        self.assertEquals(content, target_block.fields[test_data.field_name].read_from(target_block))

        with self.store.branch_setting(ModuleStoreEnum.Branch.draft_preferred):
            target_block = self.store.get_item(
                self.block_usage_key,
            )
            self.assertEquals(content, target_block.fields[test_data.field_name].read_from(target_block))

        with self.store.branch_setting(ModuleStoreEnum.Branch.published_only):
            target_block = self.store.get_item(
                self.block_usage_key,
            )
            self.assertEquals(content, target_block.fields[test_data.field_name].read_from(target_block))

    def is_detached(self, block_type):
        """
        Return True if ``block_type`` is a detached block.
        """
        return block_type in DETACHED_BLOCK_TYPES

    @ddt.data(*TESTABLE_BLOCK_TYPES)
    def test_create(self, block_type):
        self._do_create(block_type)

    # This function is split out from the test_create method so that it can be called
    # by other tests
    def _do_create(self, block_type):
        """
        Create a block of block_type (which should be a DIRECT_ONLY_CATEGORY),
        and then verify that it was created successfully, and is visible in
        both published and draft branches.
        """
        self.block_usage_key = self.course.id.make_usage_key(block_type, 'test_block')

        self.assertBlockDoesntExist()

        test_data = self.DATA_FIELDS[block_type]

        initial_field_value = test_data.initial

        with self.store.branch_setting(ModuleStoreEnum.Branch.draft_preferred):
            if self.is_detached(block_type):
                block = self.store.create_xblock(
                    self.course.runtime,
                    self.course.id,
                    self.block_usage_key.block_type,
                    block_id=self.block_usage_key.block_id
                )
                block.fields[test_data.field_name].write_to(block, initial_field_value)
                self.store.update_item(block, ModuleStoreEnum.UserID.test, allow_not_found=True)
            else:
                block = self.store.create_child(
                    user_id=ModuleStoreEnum.UserID.test,
                    parent_usage_key=self.course.scope_ids.usage_id,
                    block_type=block_type,
                    block_id=self.block_usage_key.block_id,
                    fields={test_data.field_name: initial_field_value},
                )

        self.assertBlockHasContent(test_data, initial_field_value)

    @ddt.data(*TESTABLE_BLOCK_TYPES)
    def test_update(self, block_type):
        self._do_create(block_type)

        with self.store.branch_setting(ModuleStoreEnum.Branch.draft_preferred):
            block = self.store.get_item(self.block_usage_key)

            test_data = self.DATA_FIELDS[block_type]

            updated_field_value = test_data.updated
            self.assertNotEquals(updated_field_value, block.fields[test_data.field_name].read_from(block))

            block.fields[test_data.field_name].write_to(block, updated_field_value)

            self.store.update_item(block, ModuleStoreEnum.UserID.test, allow_not_found=True)

        self.assertBlockHasContent(test_data, updated_field_value)

    @ddt.data(*TESTABLE_BLOCK_TYPES)
    def test_delete(self, block_type):
        self._do_create(block_type)

        with self.store.branch_setting(ModuleStoreEnum.Branch.draft_preferred):
            self.store.delete_item(self.block_usage_key, ModuleStoreEnum.UserID.test)

        self.assertBlockDoesntExist()


class TestSplitDirectOnlyCategorySemantics(DirectOnlyCategorySemantics):
    """
    Verify DIRECT_ONLY_CATEGORY semantics against the SplitMongoModulestore.
    """
    MODULESTORE = SPLIT_MODULESTORE_SETUP
    __test__ = True


class TestMongoDirectOnlyCategorySemantics(DirectOnlyCategorySemantics):
    """
    Verify DIRECT_ONLY_CATEGORY semantics against the MongoModulestore
    """
    MODULESTORE = MongoModulestoreBuilder()
    __test__ = True
