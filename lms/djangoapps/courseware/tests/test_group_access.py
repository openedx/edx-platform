import ddt
from stevedore.extension import Extension, ExtensionManager

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.partitions.partitions import Group, UserPartition, USER_PARTITION_SCHEME_NAMESPACE
from xmodule.modulestore.django import modulestore

import courseware.access as access
from courseware.tests.factories import UserFactory


class MemoryUserPartitionScheme(object):
    """
    In-memory partition scheme for testing.
    """
    name = "memory"

    def __init__(self):
        self.current_group = {}

    def set_group_for_user(self, user, user_partition, group):
        self.current_group.setdefault(user.id, {})[user_partition.id] = group

    def get_group_for_user(self, course_id, user, user_partition, track_function=None):  # pylint: disable=unused-argument
        """
        """
        return self.current_group.get(user.id, {}).get(user_partition.id)


@ddt.ddt
class GroupAccessTestCase(ModuleStoreTestCase):
    """
    Tests to ensure that has_access() correctly enforces the visibility
    restrictions specified in the `group_access` field of XBlocks.
    """

    def set_user_group(self, user, partition, group):
        """
        Internal DRY / shorthand.
        """
        partition.scheme.set_group_for_user(user, partition, group)

    def set_group_access(self, block, access_dict):
        """
        DRY helper.
        """
        block.group_access = access_dict
        modulestore().update_item(block, 1)

    def setUp(self):

        UserPartition.scheme_extensions = ExtensionManager.make_test_instance(
            [
                Extension(
                    "memory",
                    USER_PARTITION_SCHEME_NAMESPACE,
                    MemoryUserPartitionScheme(),
                    None
                ),
            ],
            namespace=USER_PARTITION_SCHEME_NAMESPACE
        )

        self.cat_group = Group(10, 'cats')
        self.dog_group = Group(20, 'dogs')
        self.animal_partition = UserPartition(
            0,
            'Pet Partition',
            'which animal are you?',
            [self.cat_group, self.dog_group],
            scheme=UserPartition.get_scheme("memory"),
        )

        self.red_group = Group(1000, 'red')
        self.blue_group = Group(2000, 'blue')
        self.color_partition = UserPartition(
            100,
            'Color Partition',
            'what color are you?',
            [self.red_group, self.blue_group],
            scheme=UserPartition.get_scheme("memory"),
        )

        self.course = CourseFactory.create(
            user_partitions=[self.animal_partition, self.color_partition],
        )
        self.chapter = ItemFactory.create(category='chapter', parent=self.course)
        self.section = ItemFactory.create(category='sequential', parent=self.chapter)
        self.vertical = ItemFactory.create(category='vertical', parent=self.section)
        self.component = ItemFactory.create(category='problem', parent=self.vertical)

        self.red_cat = UserFactory()  # student in red and cat groups
        self.set_user_group(self.red_cat, self.animal_partition, self.cat_group)
        self.set_user_group(self.red_cat, self.color_partition, self.red_group)

        self.blue_dog = UserFactory()  # student in blue and dog groups
        self.set_user_group(self.blue_dog, self.animal_partition, self.dog_group)
        self.set_user_group(self.blue_dog, self.color_partition, self.blue_group)

        self.gray_mouse = UserFactory()  # student in no group

    def tearDown(self):
        """
        """
        UserPartition.scheme_extensions = None

    def check_access(self, user, block, is_accessible):
        """
        DRY helper.
        """
        self.assertIs(
            access.has_access(user, 'load', block, self.course.id),
            is_accessible
        )

class SingleBlockTestMixin(object):

    def test_has_access_single_partition_single_group(self):
        """
        Access checks are correctly enforced on the block when a single group
        is specified for a single partition.
        """
        self.set_group_access(
            self.block,
            {self.animal_partition.id: [self.cat_group.id]},
        )
        self.check_access(self.red_cat, self.block, True)
        self.check_access(self.blue_dog, self.block, False)
        self.check_access(self.gray_mouse, self.block, False)

    def test_has_access_single_partition_two_groups(self):
        """
        Access checks are correctly enforced on the block when multiple groups
        are specified for a single partition.
        """
        self.set_group_access(
            self.block,
            {self.animal_partition.id: [self.cat_group.id, self.dog_group.id]},
        )
        self.check_access(self.red_cat, self.block, True)
        self.check_access(self.blue_dog, self.block, True)
        self.check_access(self.gray_mouse, self.block, False)

    def test_has_access_single_empty_partition(self):
        """
        No group access checks are enforced on the block when group_access
        declares a partition but does not specify any groups.
        """
        self.set_group_access(self.block, {self.animal_partition.id: []})
        self.check_access(self.red_cat, self.block, True)
        self.check_access(self.blue_dog, self.block, True)
        self.check_access(self.gray_mouse, self.block, True)

    def test_has_access_empty_dict(self):
        """
        No group access checks are enforced on the block when group_access is an
        empty dictionary.
        """
        self.set_group_access(self.block, {})
        self.check_access(self.red_cat, self.block, True)
        self.check_access(self.blue_dog, self.block, True)
        self.check_access(self.gray_mouse, self.block, True)

    def test_has_access_none(self):
        """
        No group access checks are enforced on the block when group_access is None.
        """
        self.set_group_access(self.block, None)
        self.check_access(self.red_cat, self.block, True)
        self.check_access(self.blue_dog, self.block, True)
        self.check_access(self.gray_mouse, self.block, True)

    def test_has_access_single_partition_group_none(self):
        """
        No group access checks are enforced on the block when group_access
        specifies a partition but its value is None.
        """
        self.set_group_access(self.block, {self.animal_partition.id: None})
        self.check_access(self.red_cat, self.block, True)
        self.check_access(self.blue_dog, self.block, True)
        self.check_access(self.gray_mouse, self.block, True)

    def test_has_access_nonexistent_partition(self):
        """
        No group access checks are enforced on the block when group_access
        specifies a partition id that does not exist in course.user_partitions.
        """
        self.set_group_access(self.block, {9: []})
        self.check_access(self.red_cat, self.block, True)
        self.check_access(self.blue_dog, self.block, True)
        self.check_access(self.gray_mouse, self.block, True)

    def test_has_access_nonexistent_group(self):
        """
        No group access checks are enforced on the block when group_access
        contains a group id that does not exist in its referenced partition.
        """
        self.set_group_access(self.block, {self.animal_partition.id: [99]})
        self.check_access(self.red_cat, self.block, True)
        self.check_access(self.blue_dog, self.block, True)
        self.check_access(self.gray_mouse, self.block, True)

    def test_multiple_partitions(self):
        """
        Group access restrictions are correctly enforced when multiple partition
        / group rules are defined.
        """
        self.set_group_access(
            self.block,
            {
                self.animal_partition.id: [self.cat_group.id],
                self.color_partition.id: [self.red_group.id],
            },
        )
        self.check_access(self.red_cat, self.block, True)
        self.check_access(self.blue_dog, self.block, False)
        self.check_access(self.gray_mouse, self.block, False)

    def test_multiple_partitions_deny_access(self):
        """
        Group access restrictions correctly deny access even when some (but not
        all) group_access rules are satisfied.
        """
        self.set_group_access(
            self.block,
            {
                self.animal_partition.id: [self.cat_group.id],
                self.color_partition.id: [self.blue_group.id],
            },
        )
        self.check_access(self.red_cat, self.block, False)
        self.check_access(self.blue_dog, self.block, False)


class ChapterGroupAccessTestCase(GroupAccessTestCase, SingleBlockTestMixin):

    @property
    def block(self): return self.chapter

class SectionGroupAccessTestCase(GroupAccessTestCase, SingleBlockTestMixin):

    @property
    def block(self): return self.section

class VerticalGroupAccessTestCase(GroupAccessTestCase, SingleBlockTestMixin):

    @property
    def block(self): return self.vertical

class ComponentGroupAccessTestCase(GroupAccessTestCase, SingleBlockTestMixin):

    @property
    def block(self): return self.component


@ddt.ddt
class ParentChildBlockTestMixin(object):

    def test_merged_groups(self):
        """
        """
        # parent is accessible to dogs and cats
        self.set_group_access(
            self.parent_block,
            {self.animal_partition.id: [self.cat_group.id, self.dog_group.id]},
        )
        # but child is accessible only to cats
        self.set_group_access(
            self.child_block,
            {self.animal_partition.id: [self.cat_group.id]},
        )

        self.assertEqual(
            access._get_merged_group_access(self.parent_block),
            {self.animal_partition.id: [self.cat_group.id, self.dog_group.id]},
        )
        self.assertEqual(
            access._get_merged_group_access(self.child_block),
            {self.animal_partition.id: [self.cat_group.id]},
        )

        self.check_access(self.red_cat, self.parent_block, True)
        self.check_access(self.blue_dog, self.parent_block, True)
        self.check_access(self.red_cat, self.child_block, True)
        self.check_access(self.blue_dog, self.child_block, False)

    def test_merged_partitions(self):
        """
        """
        # parent is accessible to dogs
        self.set_group_access(
            self.parent_block,
            {self.animal_partition.id: [self.dog_group.id]},
        )
        # child is accessible to red
        self.set_group_access(
            self.child_block,
            {self.color_partition.id: [self.red_group.id]},
        )
        self.assertEqual(
            access._get_merged_group_access(self.parent_block),
            {self.animal_partition.id: [self.dog_group.id]},
        )
        self.assertEqual(
            access._get_merged_group_access(self.child_block),
            {
                self.animal_partition.id: [self.dog_group.id],
                self.color_partition.id: [self.red_group.id],
            },
        )
        self.check_access(self.red_cat, self.parent_block, False)
        self.check_access(self.blue_dog, self.parent_block, True)
        self.check_access(self.red_cat, self.child_block, False)
        self.check_access(self.blue_dog, self.child_block, False)

    def test_merged_disjoint(self):
        """
        """
        # parent is accessible to dogs
        self.set_group_access(
            self.parent_block, {
                self.animal_partition.id: [self.dog_group.id],
            }
        )
        # child is accessible to cats
        self.set_group_access(
            self.child_block, {
                self.animal_partition.id: [self.cat_group.id],
            }
        )
        self.assertEqual(
            access._get_merged_group_access(self.parent_block),
            {self.animal_partition.id: [self.dog_group.id]},
        )
        self.assertEqual(
            access._get_merged_group_access(self.child_block),
            {self.animal_partition.id: False},
        )

        self.check_access(self.red_cat, self.parent_block, False)
        self.check_access(self.blue_dog, self.parent_block, True)
        self.check_access(self.red_cat, self.child_block, False)
        self.check_access(self.blue_dog, self.child_block, False)

    def test_staff_overrides_group_access(self):
        """
        Group access restrictions are waived for staff.
        """
        pass

    def test_anonymous(self):
        """
        Group access restrictions are enforced even with anonymous users.
        """
        pass


class ChapterParent(object):

    @property
    def parent_block(self): return self.chapter

class SectionParent(object):

    @property
    def parent_block(self): return self.section

class VerticalParent(object):

    @property
    def parent_block(self): return self.vertical

class SectionChild(object):

    @property
    def child_block(self): return self.section

class VerticalChild(object):

    @property
    def child_block(self): return self.vertical

class ComponentChild(object):

    @property
    def child_block(self): return self.component


class ChapterSectionGroupAccessTestCase(
    GroupAccessTestCase,
    ParentChildBlockTestMixin,
    ChapterParent,
    SectionChild,
): pass

class ChapterVerticalGroupAccessTestCase(
    GroupAccessTestCase,
    ParentChildBlockTestMixin,
    ChapterParent,
    VerticalChild,
): pass

class ChapterComponentGroupAccessTestCase(
    GroupAccessTestCase,
    ParentChildBlockTestMixin,
    ChapterParent,
    ComponentChild,
): pass

class SectionVerticalGroupAccessTestCase(
    GroupAccessTestCase,
    ParentChildBlockTestMixin,
    SectionParent,
    VerticalChild,
): pass

class SectionComponentGroupAccessTestCase(
    GroupAccessTestCase,
    ParentChildBlockTestMixin,
    SectionParent,
    ComponentChild,
): pass

class VerticalComponentAccessTestCase(
    GroupAccessTestCase,
    ParentChildBlockTestMixin,
    VerticalParent,
    ComponentChild,
): pass

