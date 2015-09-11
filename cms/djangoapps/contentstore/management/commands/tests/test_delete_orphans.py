"""Tests running the delete_orphan command"""

from django.core.management import call_command
from contentstore.tests.test_orphan import TestOrphanBase

from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore import ModuleStoreEnum

class TestDeleteOrphan(TestOrphanBase):
    """
    Tests for running the delete_orphan management command.
    Inherits from TestOrphan in order to use its setUp method.
    """
    def setUp(self):
        super(TestDeleteOrphan, self).setUp()
        self.course_id = unicode(self.course.id)

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

    def test_delete_orphans_published_branch(self):
        """
        Tests that if there are orphans only on the published branch,
        running delete orphans with a course key that specifies
        the published branch will delete the published orphan
        """
        course = CourseFactory.create(default_store=ModuleStoreEnum.Type.split)
        # create an orphan
        orphan = self.store.create_item(self.user.id, course.id, 'html', "OrphanHtml")
        self.store.publish(orphan.location, self.user.id)

        # grab the published branch of the course
        published_branch = course.id.for_branch(
            ModuleStoreEnum.BranchName.published
        )

        # assert that this orphan is present in both branches
        self.assertOrphanCount(course.id, 1)
        self.assertOrphanCount(published_branch, 1)

        # delete this orphan from the draft branch without
        # auto-publishing this change to the published draft
        self.store.delete_item(
            orphan.location, self.user.id, skip_auto_publish=True
        )

        # now there should be no orphans in the draft branch, but
        # there should be one in published
        self.assertOrphanCount(course.id, 0)
        self.assertOrphanCount(published_branch, 1)

        # call delete orphans, specifying the published branch
        # of the course
        call_command('delete_orphans', unicode(published_branch), 'commit')

        # now all orphans should be deleted
        self.assertOrphanCount(course.id, 0)
        self.assertOrphanCount(published_branch, 0)

    def assertOrphanCount(self, course_key, number):
        self.assertEqual(len(self.store.get_orphans(course_key)), number)
