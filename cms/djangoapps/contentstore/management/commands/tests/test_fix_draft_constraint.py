"""Tests running the fix_draft_constraint command"""

from django.core.management import call_command
from django.core.management.base import CommandError
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase, ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
import ddt


@ddt.ddt
class TestFixDraftConstraint(ModuleStoreTestCase):

    # @classmethod
    def setUp(self):
        super(TestFixDraftConstraint, self).setUp()
        self.course_satisfies = CourseFactory.create(default_store=ModuleStoreEnum.Type.split)
        self.course_does_not_satisfy = CourseFactory.create(default_store=ModuleStoreEnum.Type.split)

        ItemFactory.create(
            parent_location=self.course_does_not_satisfy.location,
            category="sequential",
        )

        self.split_store = modulestore()._get_modulestore_for_courselike(self.course_satisfies.id)

        # add something to the published branch of course_does_not_satisfy
        draft_location = self.split_store._map_revision_to_branch(
            self.course_does_not_satisfy.id,
            ModuleStoreEnum.RevisionOption.draft_only,
        )

        not_sat_draft_structure = self.split_store._lookup_course(draft_location).structure
        not_sat_head = self.split_store._get_index_if_valid(draft_location)

        new_not_sat_draft_structure = self.split_store.version_structure(
            draft_location, not_sat_draft_structure, ModuleStoreEnum.UserID.mgmt_command
        )
        draft_seq = [
            key for (key, value) in new_not_sat_draft_structure['blocks'].iteritems()
            if value.block_type == "sequential"
        ][0]

        del new_not_sat_draft_structure['blocks'][draft_seq]

        self.split_store.update_structure(draft_location, new_not_sat_draft_structure)

        if not_sat_head is not None:
            self.split_store._update_head(
                draft_location,
                not_sat_head,
                draft_location.branch,
                new_not_sat_draft_structure['_id'],
            )

    # (Satisfies Draft Constraint, commit)
    @ddt.data((True, True), (True, False), (False, False))
    @ddt.unpack
    def test_fix_draft_constraint_no_op(self, satisfies, commit):
        """
        Tests that running the command in these scenarios results in a noop:
            1) Course satisfies constraint; we run the command with 'commit'
            2) Course satisfies constraint; we run the command without 'commit'
            3) Course does not satisfy constraint; we run the command without 'commit'
        """
        course = self.course_does_not_satisfy
        if satisfies:
            course = self.course_satisfies

        draft_location = self.split_store._map_revision_to_branch(
            course.id, ModuleStoreEnum.RevisionOption.draft_only
        )
        draft_structure = self.split_store._lookup_course(draft_location).structure
        draft_head = self.split_store._get_index_if_valid(draft_location)

        args = ['fix_draft_constraint', unicode(course.id)]
        if commit:
            args.append('commit')

        call_command(*args)
        new_draft_location = self.split_store._map_revision_to_branch(
            course.id, ModuleStoreEnum.RevisionOption.draft_only
        )

        new_draft_structure = self.split_store._lookup_course(draft_location).structure

        new_draft_head = self.split_store._get_index_if_valid(draft_location)

        # the location should be the same
        self.assertEqual(draft_location, new_draft_location)
        # the structure should be the same
        self.assertEqual(draft_structure, new_draft_structure)
        # and the course index should be the same
        self.assertEqual(draft_head, new_draft_head)

    # @SharedModuleStoreTestCase.modifies_courseware
    def test_fix_draft_constraint_commit(self):
        """
        Tests that running the command WITH the 'commit' argument
        when the course does not satisfy the draft constraint
        results in the "head" being changed and the draft constraint being
        satisfied.
        """
        course = self.course_does_not_satisfy

        draft_location, draft_structure, draft_head = self.get_branch_information(
            self.split_store, course, ModuleStoreEnum.RevisionOption.draft_only
        )

        call_command(
            'fix_draft_constraint',
            unicode(self.course_does_not_satisfy.id),
            'commit'
        )

        new_location, new_structure, new_head = self.get_branch_information(
            self.split_store, course, ModuleStoreEnum.RevisionOption.draft_only
        )

        self.assertEqual(draft_location, new_location)
        self.assertNotEqual(draft_structure, new_structure)
        self.assertNotEqual(draft_head, new_head)

    def test_fix_draft_constraint_non_split_course(self):
        non_split_course = CourseFactory(default_store=ModuleStoreEnum.Type.mongo)
        with self.assertRaises(SystemExit):
            call_command('fix_draft_constraint', unicode(non_split_course.id), 'commit')


    def get_branch_information(self, store, course, branch):
        location = store._map_revision_to_branch(course.id, branch)
        structure = store._lookup_course(location).structure
        head = store._get_index_if_valid(location)
        return location, structure, head