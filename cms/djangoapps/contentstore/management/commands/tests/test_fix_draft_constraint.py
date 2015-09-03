"""Tests running the fix_draft_constraint command"""

from contextlib import contextmanager
import ddt
from django.core.management import call_command
from django.core.management.base import CommandError

from contentstore.views.item import fix_draft_constraint
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory


@ddt.ddt
class TestFixDraftConstraint(SharedModuleStoreTestCase):
    """
    Tests for the fix_draft_constraint management command.
    """

    @classmethod
    def setUpClass(cls):
        super(TestFixDraftConstraint, cls).setUpClass()
        # pylint: disable=protected-access
        cls.split_store = cls.store._get_modulestore_by_type(ModuleStoreEnum.Type.split)

        # create one course that should satisfy the draft constraint
        cls.course_satisfies = CourseFactory.create(default_store=ModuleStoreEnum.Type.split)

        # and one that shouldn't
        cls.course_does_not_satisfy = cls.create_course_that_fails_constraint()

    # (Satisfies Draft Constraint, commit)
    @ddt.data((True, True), (True, False), (False, False))
    @ddt.unpack
    def test_fix_draft_constraint_noop(self, satisfies, commit):
        """
        Tests that running the command in these scenarios results in a noop:
            1) Course satisfies constraint; we run the command with 'commit'
            2) Course satisfies constraint; we run the command without 'commit'
            3) Course does not satisfy constraint; we run the command without 'commit'
        """
        course = self.course_does_not_satisfy
        if satisfies:
            course = self.course_satisfies

        args = ['fix_draft_constraint', unicode(course.id)]
        if commit:
            args.append('commit')

        with self.assert_branch_unchanged(self.split_store, course, ModuleStoreEnum.RevisionOption.draft_only):
            with self.assert_branch_unchanged(self.split_store, course, ModuleStoreEnum.RevisionOption.published_only):
                call_command(*args)


    @SharedModuleStoreTestCase.modifies_courseware
    def test_fix_draft_constraint_commit(self):
        """
        Tests that running the command WITH the 'commit' argument
        when the course does not satisfy the draft constraint
        results in the "head" being changed and the draft constraint being
        satisfied.
        """
        course = self.course_does_not_satisfy

        draft_location, draft_structure = self.get_branch_information(
            self.split_store, course, ModuleStoreEnum.RevisionOption.draft_only
        )

        with self.assert_branch_unchanged(
            self.split_store,
            course,
            ModuleStoreEnum.RevisionOption.published_only,
        ):
            call_command(
                'fix_draft_constraint',
                unicode(self.course_does_not_satisfy.id),
                'commit'
            )

        new_location, new_structure = self.get_branch_information(
            self.split_store, course, ModuleStoreEnum.RevisionOption.draft_only
        )

        self.assertEqual(draft_location, new_location)
        self.assertNotEqual(draft_structure, new_structure)

    def test_fix_draft_constraint_non_split_course(self):
        """
        Trying to run fix_draft_constraint on a non split course will
        result in an error.
        """
        non_split_course = CourseFactory(default_store=ModuleStoreEnum.Type.mongo)
        with self.assertRaises(SystemExit):
            call_command('fix_draft_constraint', unicode(non_split_course.id), 'commit')


    @classmethod
    def create_course_that_fails_constraint(cls):
        """
        Create a course that has a draft-branch block_id that isn't also
        in the published branch.
        """
        course = CourseFactory.create(default_store=ModuleStoreEnum.Type.split)
        item = ItemFactory.create(
            parent_location=course.location,
            category="sequential",
        )

        # pylint: disable=protected-access
        draft_location = cls.split_store._map_revision_to_branch(
            course.id,
            ModuleStoreEnum.RevisionOption.draft_only,
        )

        # pylint: disable=protected-access
        draft_structure = cls.split_store._lookup_course(draft_location).structure
        # pylint: disable=protected-access
        course_index = cls.split_store._get_index_if_valid(draft_location)

        new_draft_structure = cls.split_store.version_structure(
            draft_location, draft_structure, ModuleStoreEnum.UserID.mgmt_command
        )

        draft_item_block_keys = [
            block_key for block_key in new_draft_structure['blocks']
            if block_key.id == item.location.block_id
        ]

        assert len(draft_item_block_keys) == 1

        draft_item_block_key = draft_item_block_keys[0]

        del new_draft_structure['blocks'][draft_item_block_key]

        cls.split_store.update_structure(draft_location, new_draft_structure)

        # pylint: disable=protected-access
        cls.split_store._update_head(
            draft_location,
            course_index,
            draft_location.branch,
            new_draft_structure['_id'],
        )

        return course

    def get_branch_information(self, store, course, branch):
        """
        Get the location and the structure of a branch.
        """
        # pylint: disable=protected-access
        location = store._map_revision_to_branch(course.id, branch)
        structure = store._lookup_course(location).structure
        return location, structure

    @contextmanager
    def assert_branch_unchanged(self, store, course, branch):
        """
        This is a context manager that asserts that a branch
        remains unchanged while the code it wraps executes.
        """
        location, structure = self.get_branch_information(
            self.split_store, course, branch
        )
        yield
        new_location, new_structure = self.get_branch_information(
            self.split_store, course, branch
        )
        self.assertEqual(location, new_location)
        self.assertEqual(structure, new_structure)
