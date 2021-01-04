"""Tests running the delete_orphan command"""


import ddt
import six
from django.core.management import CommandError, call_command

from cms.djangoapps.contentstore.tests.test_orphan import TestOrphanBase
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.factories import CourseFactory


@ddt.ddt
class TestDeleteOrphan(TestOrphanBase):
    """
    Tests for running the delete_orphan management command.
    Inherits from TestOrphan in order to use its setUp method.
    """
    def test_no_args(self):
        """
        Test delete_orphans command with no arguments
        """
        if six.PY2:
            errstring = 'Error: too few arguments'
        else:
            errstring = 'Error: the following arguments are required: course_id'
        with self.assertRaisesRegex(CommandError, errstring):
            call_command('delete_orphans')

    @ddt.data(ModuleStoreEnum.Type.split, ModuleStoreEnum.Type.mongo)
    def test_delete_orphans_no_commit(self, default_store):
        """
        Tests that running the command without a '--commit' argument
        results in no orphans being deleted
        """
        course = self.create_course_with_orphans(default_store)
        call_command('delete_orphans', six.text_type(course.id))
        self.assertTrue(self.store.has_item(course.id.make_usage_key('html', 'multi_parent_html')))
        self.assertTrue(self.store.has_item(course.id.make_usage_key('vertical', 'OrphanVert')))
        self.assertTrue(self.store.has_item(course.id.make_usage_key('chapter', 'OrphanChapter')))
        self.assertTrue(self.store.has_item(course.id.make_usage_key('html', 'OrphanHtml')))

    @ddt.data(ModuleStoreEnum.Type.split, ModuleStoreEnum.Type.mongo)
    def test_delete_orphans_commit(self, default_store):
        """
        Tests that running the command WITH the '--commit' argument
        results in the orphans being deleted
        """
        course = self.create_course_with_orphans(default_store)

        call_command('delete_orphans', six.text_type(course.id), '--commit')

        # make sure this module wasn't deleted
        self.assertTrue(self.store.has_item(course.id.make_usage_key('html', 'multi_parent_html')))

        # and make sure that these were
        self.assertFalse(self.store.has_item(course.id.make_usage_key('vertical', 'OrphanVert')))
        self.assertFalse(self.store.has_item(course.id.make_usage_key('chapter', 'OrphanChapter')))
        self.assertFalse(self.store.has_item(course.id.make_usage_key('html', 'OrphanHtml')))

    def test_delete_orphans_published_branch_split(self):
        """
        Tests that if there are orphans only on the published branch,
        running delete orphans with a course key that specifies
        the published branch will delete the published orphan
        """
        course, orphan = self.create_split_course_with_published_orphan()
        published_branch = course.id.for_branch(ModuleStoreEnum.BranchName.published)

        items_in_published = self.store.get_items(published_branch)
        items_in_draft_preferred = self.store.get_items(course.id)

        # call delete orphans, specifying the published branch
        # of the course
        call_command('delete_orphans', six.text_type(published_branch), '--commit')

        # now all orphans should be deleted
        self.assertOrphanCount(course.id, 0)
        self.assertOrphanCount(published_branch, 0)
        self.assertNotIn(orphan, self.store.get_items(published_branch))
        # we should have one fewer item in the published branch of the course
        self.assertEqual(
            len(items_in_published) - 1,
            len(self.store.get_items(published_branch)),
        )
        # and the same amount of items in the draft branch of the course
        self.assertEqual(
            len(items_in_draft_preferred),
            len(self.store.get_items(course.id)),
        )

    def create_split_course_with_published_orphan(self):
        """
        Helper to create a split course with a published orphan
        """
        course = CourseFactory.create(default_store=ModuleStoreEnum.Type.split)
        # create an orphan
        orphan = self.store.create_item(
            self.user.id, course.id, 'html', "PublishedOnlyOrphan"
        )
        self.store.publish(orphan.location, self.user.id)

        # grab the published branch of the course
        published_branch = course.id.for_branch(
            ModuleStoreEnum.BranchName.published
        )

        # assert that this orphan is present in both branches
        self.assertOrphanCount(course.id, 1)
        self.assertOrphanCount(published_branch, 1)

        # delete this orphan from the draft branch without
        # auto-publishing this change to the published branch
        self.store.delete_item(
            orphan.location, self.user.id, skip_auto_publish=True
        )

        # now there should be no orphans in the draft branch, but
        # there should be one in published
        self.assertOrphanCount(course.id, 0)
        self.assertOrphanCount(published_branch, 1)
        self.assertIn(orphan.location, [x.location for x in self.store.get_items(published_branch)])

        return course, orphan
