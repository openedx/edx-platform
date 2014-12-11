"""
Tests of the LMS XBlock Mixin
"""
import ddt
from django.conf import settings

from xblock.validation import ValidationMessage
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.modulestore_settings import update_module_store_settings
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.partitions.partitions import Group, UserPartition


class LmsXBlockMixinTestCase(ModuleStoreTestCase):
    """
    Base class for XBlock mixin tests cases. A simple course with a single user partition is created
    in setUp for all subclasses to use.
    """
    def build_course(self):
        """
        Build up a course tree with a UserPartition.
        """
        # pylint: disable=attribute-defined-outside-init
        self.user_partition = UserPartition(
            0,
            'first_partition',
            'First Partition',
            [
                Group(0, 'alpha'),
                Group(1, 'beta')
            ]
        )
        self.group1 = self.user_partition.groups[0]    # pylint: disable=no-member
        self.group2 = self.user_partition.groups[1]    # pylint: disable=no-member
        self.course = CourseFactory.create(user_partitions=[self.user_partition])
        self.section = ItemFactory.create(parent=self.course, category='chapter', display_name='Test Section')
        self.subsection = ItemFactory.create(parent=self.section, category='sequential', display_name='Test Subsection')
        self.vertical = ItemFactory.create(parent=self.subsection, category='vertical', display_name='Test Unit')
        self.video = ItemFactory.create(parent=self.vertical, category='video', display_name='Test Video 1')


class XBlockValidationTest(LmsXBlockMixinTestCase):
    """
    Unit tests for XBlock validation
    """
    def setUp(self):
        super(XBlockValidationTest, self).setUp()
        self.build_course()

    def verify_validation_message(self, message, expected_message, expected_message_type):
        """
        Verify that the validation message has the expected validation message and type.
        """
        self.assertEqual(message.text, expected_message)
        self.assertEqual(message.type, expected_message_type)

    def test_validate_full_group_access(self):
        """
        Test the validation messages produced for an xblock with full group access.
        """
        validation = self.video.validate()
        self.assertEqual(len(validation.messages), 0)

    def test_validate_restricted_group_access(self):
        """
        Test the validation messages produced for an xblock with a valid group access restriction
        """
        self.video.group_access[self.user_partition.id] = [self.group1.id, self.group2.id]  # pylint: disable=no-member
        validation = self.video.validate()
        self.assertEqual(len(validation.messages), 0)

    def test_validate_invalid_user_partitions(self):
        """
        Test the validation messages produced for an xblock referring to non-existent user partitions.
        """
        self.video.group_access[999] = [self.group1.id]
        validation = self.video.validate()
        self.assertEqual(len(validation.messages), 1)
        self.verify_validation_message(
            validation.messages[0],
            u"This component refers to deleted or invalid content group configurations.",
            ValidationMessage.ERROR,
        )

        # Now add a second invalid user partition and validate again.
        # Note that even though there are two invalid configurations,
        # only a single error message will be returned.
        self.video.group_access[998] = [self.group2.id]
        validation = self.video.validate()
        self.assertEqual(len(validation.messages), 1)
        self.verify_validation_message(
            validation.messages[0],
            u"This component refers to deleted or invalid content group configurations.",
            ValidationMessage.ERROR,
        )

    def test_validate_invalid_groups(self):
        """
        Test the validation messages produced for an xblock referring to non-existent groups.
        """
        self.video.group_access[self.user_partition.id] = [self.group1.id, 999]    # pylint: disable=no-member
        validation = self.video.validate()
        self.assertEqual(len(validation.messages), 1)
        self.verify_validation_message(
            validation.messages[0],
            u"This component refers to deleted or invalid content groups.",
            ValidationMessage.ERROR,
        )

        # Now try again with two invalid group ids
        self.video.group_access[self.user_partition.id] = [self.group1.id, 998, 999]    # pylint: disable=no-member
        validation = self.video.validate()
        self.assertEqual(len(validation.messages), 1)
        self.verify_validation_message(
            validation.messages[0],
            u"This component refers to deleted or invalid content groups.",
            ValidationMessage.ERROR,
        )


class OpenAssessmentBlockMixinTestCase(ModuleStoreTestCase):
    """
    Tests for OpenAssessmentBlock mixin.
    """

    def setUp(self):
        super(OpenAssessmentBlockMixinTestCase, self).setUp()
        self.course = CourseFactory.create()
        self.section = ItemFactory.create(parent=self.course, category='chapter', display_name='Test Section')
        self.open_assessment = ItemFactory.create(
            parent=self.section,
            category="openassessment",
            display_name="untitled",
        )

    def test_has_score(self):
        """
        Test has_score is true for ora2 problems.
        """
        self.assertTrue(self.open_assessment.has_score)


@ddt.ddt
class XBlockGetParentTest(LmsXBlockMixinTestCase):
    """
    Test that XBlock.get_parent returns correct results with each modulestore
    backend.
    """
    def _pre_setup(self):
        # load the one xml course into the xml store
        update_module_store_settings(
            settings.MODULESTORE,
            mappings={'edX/toy/2012_Fall': ModuleStoreEnum.Type.xml},
            xml_store_options={
                'data_dir': settings.COMMON_TEST_DATA_ROOT  # where toy course lives
            },
        )
        super(XBlockGetParentTest, self)._pre_setup()

    @ddt.data(ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split, ModuleStoreEnum.Type.xml)
    def test_parents(self, modulestore_type):
        with self.store.default_store(modulestore_type):

            # setting up our own local course tree here, since it needs to be
            # created with the correct modulestore type.

            if modulestore_type == 'xml':
                course_key = self.store.make_course_key('edX', 'toy', '2012_Fall')
            else:
                course_key = self.create_toy_course('edX', 'toy', '2012_Fall_copy')
            course = self.store.get_course(course_key)

            self.assertIsNone(course.get_parent())

            def recurse(parent):
                """
                Descend the course tree and ensure the result of get_parent()
                is the expected one.
                """
                visited = []
                for child in parent.get_children():
                    self.assertEqual(parent.location, child.get_parent().location)
                    visited.append(child)
                    visited += recurse(child)
                return visited

            visited = recurse(course)
            self.assertEqual(len(visited), 28)

    @ddt.data(ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split)
    def test_parents_draft_content(self, modulestore_type):
        # move the video to the new vertical
        with self.store.default_store(modulestore_type):
            self.build_course()
            new_vertical = ItemFactory.create(parent=self.subsection, category='vertical', display_name='New Test Unit')
            child_to_move_location = self.video.location.for_branch(None)
            new_parent_location = new_vertical.location.for_branch(None)
            old_parent_location = self.vertical.location.for_branch(None)

            with self.store.branch_setting(ModuleStoreEnum.Branch.draft_preferred):
                self.assertIsNone(self.course.get_parent())

                with self.store.bulk_operations(self.course.id):
                    user_id = ModuleStoreEnum.UserID.test

                    old_parent = self.store.get_item(old_parent_location)
                    old_parent.children.remove(child_to_move_location)
                    self.store.update_item(old_parent, user_id)

                    new_parent = self.store.get_item(new_parent_location)
                    new_parent.children.append(child_to_move_location)
                    self.store.update_item(new_parent, user_id)

                    # re-fetch video from draft store
                    video = self.store.get_item(child_to_move_location)

                    self.assertEqual(
                        new_parent_location,
                        video.get_parent().location
                    )
            with self.store.branch_setting(ModuleStoreEnum.Branch.published_only):
                # re-fetch video from published store
                video = self.store.get_item(child_to_move_location)
                self.assertEqual(
                    old_parent_location,
                    video.get_parent().location.for_branch(None)
                )


class RenamedTuple(tuple):  # pylint: disable=incomplete-protocol
    """
    This class is only used to allow overriding __name__ on the tuples passed
    through ddt, in order to have the generated test names make sense.
    """
    pass


def ddt_named(parent, child):
    """
    Helper to get more readable dynamically-generated test names from ddt.
    """
    args = RenamedTuple([parent, child])
    setattr(args, '__name__', 'parent_{}_child_{}'.format(parent, child))
    return args


@ddt.ddt
class XBlockMergedGroupAccessTest(LmsXBlockMixinTestCase):
    """
    Test that XBlock.merged_group_access is computed correctly according to
    our access control rules.
    """

    PARTITION_1 = 1
    PARTITION_1_GROUP_1 = 11
    PARTITION_1_GROUP_2 = 12

    PARTITION_2 = 2
    PARTITION_2_GROUP_1 = 21
    PARTITION_2_GROUP_2 = 22

    PARENT_CHILD_PAIRS = (
        ddt_named('section', 'subsection'),
        ddt_named('section', 'vertical'),
        ddt_named('section', 'video'),
        ddt_named('subsection', 'vertical'),
        ddt_named('subsection', 'video'),
    )

    def setUp(self):
        super(XBlockMergedGroupAccessTest, self).setUp()
        self.build_course()

    def set_group_access(self, block, access_dict):
        """
        DRY helper.
        """
        block.group_access = access_dict
        block.runtime.modulestore.update_item(block, 1)

    @ddt.data(*PARENT_CHILD_PAIRS)
    @ddt.unpack
    def test_intersecting_groups(self, parent, child):
        """
        When merging group_access on a block, the resulting group IDs for each
        partition is the intersection of the group IDs defined for that
        partition across all ancestor blocks (including this one).
        """
        parent_block = getattr(self, parent)
        child_block = getattr(self, child)

        self.set_group_access(parent_block, {self.PARTITION_1: [self.PARTITION_1_GROUP_1, self.PARTITION_1_GROUP_2]})
        self.set_group_access(child_block, {self.PARTITION_1: [self.PARTITION_1_GROUP_2]})

        self.assertEqual(
            parent_block.merged_group_access,
            {self.PARTITION_1: [self.PARTITION_1_GROUP_1, self.PARTITION_1_GROUP_2]},
        )
        self.assertEqual(
            child_block.merged_group_access,
            {self.PARTITION_1: [self.PARTITION_1_GROUP_2]},
        )

    @ddt.data(*PARENT_CHILD_PAIRS)
    @ddt.unpack
    def test_disjoint_groups(self, parent, child):
        """
        When merging group_access on a block, if the intersection of group IDs
        for a partition is empty, the merged value for that partition is False.
        """
        parent_block = getattr(self, parent)
        child_block = getattr(self, child)

        self.set_group_access(parent_block, {self.PARTITION_1: [self.PARTITION_1_GROUP_1]})
        self.set_group_access(child_block, {self.PARTITION_1: [self.PARTITION_1_GROUP_2]})

        self.assertEqual(
            parent_block.merged_group_access,
            {self.PARTITION_1: [self.PARTITION_1_GROUP_1]},
        )
        self.assertEqual(
            child_block.merged_group_access,
            {self.PARTITION_1: False},
        )

    def test_disjoint_groups_no_override(self):
        """
        Special case of the above test - ensures that `False` propagates down
        to the block being queried even if blocks further down in the hierarchy
        try to override it.
        """
        self.set_group_access(self.section, {self.PARTITION_1: [self.PARTITION_1_GROUP_1]})
        self.set_group_access(self.subsection, {self.PARTITION_1: [self.PARTITION_1_GROUP_2]})
        self.set_group_access(self.vertical, {self.PARTITION_1: [self.PARTITION_1_GROUP_1, self.PARTITION_1_GROUP_2]})

        self.assertEqual(
            self.vertical.merged_group_access,
            {self.PARTITION_1: False},
        )
        self.assertEqual(
            self.video.merged_group_access,
            {self.PARTITION_1: False},
        )

    @ddt.data(*PARENT_CHILD_PAIRS)
    @ddt.unpack
    def test_union_partitions(self, parent, child):
        """
        When merging group_access on a block, the result's keys (partitions)
        are the union of all partitions specified across all ancestor blocks
        (including this one).
        """
        parent_block = getattr(self, parent)
        child_block = getattr(self, child)

        self.set_group_access(parent_block, {self.PARTITION_1: [self.PARTITION_1_GROUP_1]})
        self.set_group_access(child_block, {self.PARTITION_2: [self.PARTITION_1_GROUP_2]})

        self.assertEqual(
            parent_block.merged_group_access,
            {self.PARTITION_1: [self.PARTITION_1_GROUP_1]},
        )
        self.assertEqual(
            child_block.merged_group_access,
            {self.PARTITION_1: [self.PARTITION_1_GROUP_1], self.PARTITION_2: [self.PARTITION_1_GROUP_2]},
        )
