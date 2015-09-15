"""Tests running the delete_orphan command"""

import ddt
from django.core.management import call_command
from contentstore.tests.test_orphan import TestOrphanBase
from xmodule.modulestore import ModuleStoreEnum


@ddt.ddt
class TestDeleteOrphan(TestOrphanBase):
    """
    Tests for running the delete_orphan management command.
    Inherits from TestOrphan in order to use its setUp method.
    """
    @ddt.data(ModuleStoreEnum.Type.split, ModuleStoreEnum.Type.mongo)
    def test_delete_orphans_no_commit(self, default_store):
        """
        Tests that running the command without a 'commit' argument
        results in no orphans being deleted
        """
        course = self.create_course_with_orphans(default_store)
        call_command('delete_orphans', unicode(course.id))
        self.assertTrue(self.store.has_item(course.id.make_usage_key('html', 'multi_parent_html')))
        self.assertTrue(self.store.has_item(course.id.make_usage_key('vertical', 'OrphanVert')))
        self.assertTrue(self.store.has_item(course.id.make_usage_key('chapter', 'OrphanChapter')))
        self.assertTrue(self.store.has_item(course.id.make_usage_key('html', 'OrphanHtml')))

    @ddt.data(ModuleStoreEnum.Type.split, ModuleStoreEnum.Type.mongo)
    def test_delete_orphans_commit(self, default_store):
        """
        Tests that running the command WITH the 'commit' argument
        results in the orphans being deleted
        """
        course = self.create_course_with_orphans(default_store)

        call_command('delete_orphans', unicode(course.id), 'commit')

        # make sure this module wasn't deleted
        self.assertTrue(self.store.has_item(course.id.make_usage_key('html', 'multi_parent_html')))

        # and make sure that these were
        self.assertFalse(self.store.has_item(course.id.make_usage_key('vertical', 'OrphanVert')))
        self.assertFalse(self.store.has_item(course.id.make_usage_key('chapter', 'OrphanChapter')))
        self.assertFalse(self.store.has_item(course.id.make_usage_key('html', 'OrphanHtml')))
