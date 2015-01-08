"""Tests running the delete_orphan command"""

from django.core.management import call_command
from contentstore.tests.test_orphan import TestOrphanBase


class TestDeleteOrphan(TestOrphanBase):
    """
    Tests for running the delete_orphan management command.
    Inherits from TestOrphan in order to use its setUp method.
    """
    def setUp(self):
        super(TestDeleteOrphan, self).setUp()
        self.course_id = self.course.id.to_deprecated_string()

    def test_delete_orphans_no_commit(self):
        """
        Tests that running the command without a 'commit' argument
        results in no orphans being deleted
        """
        call_command('delete_orphans', self.course_id)
        self.assertTrue(self.store.has_item(self.course.id.make_usage_key('html', 'multi_parent_html')))
        self.assertTrue(self.store.has_item(self.course.id.make_usage_key('vertical', 'OrphanVert')))
        self.assertTrue(self.store.has_item(self.course.id.make_usage_key('chapter', 'OrphanChapter')))
        self.assertTrue(self.store.has_item(self.course.id.make_usage_key('html', 'OrphanHtml')))

    def test_delete_orphans_commit(self):
        """
        Tests that running the command WITH the 'commit' argument
        results in the orphans being deleted
        """
        call_command('delete_orphans', self.course_id, 'commit')

        # make sure this module wasn't deleted
        self.assertTrue(self.store.has_item(self.course.id.make_usage_key('html', 'multi_parent_html')))

        # and make sure that these were
        self.assertFalse(self.store.has_item(self.course.id.make_usage_key('vertical', 'OrphanVert')))
        self.assertFalse(self.store.has_item(self.course.id.make_usage_key('chapter', 'OrphanChapter')))
        self.assertFalse(self.store.has_item(self.course.id.make_usage_key('html', 'OrphanHtml')))
