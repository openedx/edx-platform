"""
    Test split_draft modulestore
"""
import unittest
import uuid
from xmodule.modulestore.split_mongo.split_draft import DraftVersioningModuleStore
from xmodule.modulestore import ModuleStoreEnum
from opaque_keys.edx.locator import CourseLocator
from xmodule.modulestore.inheritance import InheritanceMixin
from xmodule.x_module import XModuleMixin
from xmodule.modulestore.tests.test_split_modulestore import SplitModuleTest
from xmodule.modulestore.tests.mongo_connection import MONGO_PORT_NUM, MONGO_HOST

# pylint: disable=W0613
def render_to_template_mock(*args):
    pass


class TestDraftVersioningModuleStore(unittest.TestCase):
    def setUp(self):
        super(TestDraftVersioningModuleStore, self).setUp()
        self.module_store = DraftVersioningModuleStore(
            contentstore=None,
            doc_store_config={
                'host': MONGO_HOST,
                'port': MONGO_PORT_NUM,
                'db': 'test_xmodule',
                'collection': 'modulestore{0}'.format(uuid.uuid4().hex[:5]),
            },
            fs_root='',
            default_class='xmodule.raw_module.RawDescriptor',
            render_template=render_to_template_mock,
            xblock_mixins=(InheritanceMixin, XModuleMixin),
        )
        self.addCleanup(self.module_store._drop_database)

        SplitModuleTest.bootstrapDB(self.module_store)

    def test_has_changes(self):
        """
        Tests that has_changes() only returns true when changes are present
        """
        draft_course = CourseLocator(
            org='testx', course='GreekHero', run='run', branch=ModuleStoreEnum.BranchName.draft
        )
        head = draft_course.make_usage_key('course', 'head12345')
        dummy_user = ModuleStoreEnum.UserID.test

        # Not yet published, so changes are present
        self.assertTrue(self.module_store.has_changes(head))

        # Publish and verify that there are no unpublished changes
        self.module_store.publish(head, dummy_user)
        self.assertFalse(self.module_store.has_changes(head))

        # Change the course, then check that there now are changes
        course = self.module_store.get_item(head)
        course.show_calculator = not course.show_calculator
        self.module_store.update_item(course, dummy_user)
        self.assertTrue(self.module_store.has_changes(head))

        # Publish and verify again
        self.module_store.publish(head, dummy_user)
        self.assertFalse(self.module_store.has_changes(head))
