# pylint: disable=attribute-defined-outside-init, protected-access
"""
Tests for UserPartitionTransformer.
"""
import ddt

from openedx.core.djangoapps.course_groups.partition_scheme import CohortPartitionScheme
from openedx.core.djangoapps.course_groups.tests.helpers import CohortFactory, config_course_cohorts
from openedx.core.djangoapps.course_groups.cohorts import add_user_to_cohort
from openedx.core.djangoapps.course_groups.views import link_cohort_to_partition_group
from student.tests.factories import CourseEnrollmentFactory
from xmodule.partitions.partitions import Group, UserPartition

from ...api import get_course_blocks
from ..user_partitions import UserPartitionTransformer, _MergedGroupAccess
from .test_helpers import CourseStructureTestCase


class UserPartitionTestMixin(object):
    """
    Helper Mixin for testing user partitions.
    """
    def setup_groups_partitions(self, num_user_partitions=1, num_groups=4):
        """
        Sets up groups and user partitions for testing.
        """
        # Set up groups
        self.groups = []
        for group_num in range(1, num_groups + 1):
            self.groups.append(Group(group_num, 'Group ' + unicode(group_num)))

        # Set up user partitions
        self.user_partitions = []
        for user_partition_num in range(1, num_user_partitions + 1):
            user_partition = UserPartition(
                id=user_partition_num,
                name='Partition ' + unicode(user_partition_num),
                description='This is partition ' + unicode(user_partition_num),
                groups=self.groups,
                scheme=CohortPartitionScheme
            )
            user_partition.scheme.name = "cohort"
            self.user_partitions.append(user_partition)

    def setup_chorts(self, course):
        """
        Sets up a cohort for each previously created user partition.
        """
        for user_partition in self.user_partitions:
            config_course_cohorts(course, is_cohorted=True)
            self.cohorts = []
            for group in self.groups:
                cohort = CohortFactory(course_id=course.id)
                self.cohorts.append(cohort)
                link_cohort_to_partition_group(
                    cohort,
                    user_partition.id,
                    group.id,
                )


@ddt.ddt
class UserPartitionTransformerTestCase(UserPartitionTestMixin, CourseStructureTestCase):
    """
    UserPartitionTransformer Test
    """
    def setUp(self):
        """
        Setup course structure and create user for user partition
        transformer test.
        """
        super(UserPartitionTransformerTestCase, self).setUp()

        # Set up user partitions and groups.
        self.setup_groups_partitions()
        self.user_partition = self.user_partitions[0]

        # Build course.
        self.course_hierarchy = self.get_course_hierarchy()
        self.blocks = self.build_course(self.course_hierarchy)
        self.course = self.blocks['course']

        # Enroll user in course.
        CourseEnrollmentFactory.create(user=self.user, course_id=self.course.id, is_active=True)

        # Set up cohorts.
        self.setup_chorts(self.course)

        self.transformer = UserPartitionTransformer()

    def get_course_hierarchy(self):
        """
        Returns a course hierarchy to test with.
        """
        #                                     course
        #                                  /          \
        #                                 /            \
        #                      A[1, 2, 3]                B
        #                     /  |      \                |
        #                   /    |       \               |
        #                 /      |        \              |
        #           C[1, 2]    D[2, 3]     E            /
        #         / |     \      |        / \          /
        #        /  |     \      |       /   \        /
        #       /   |     \      |      /     \      /
        #     F   G[1]   H[2]    I     J     K[4]   /
        #        /   \    /                  /  \  /
        #       /    \   /                  /   \ /
        #      /     \  /                  /    \/
        #  L[1, 2]  M[1, 2, 3]            N     O
        #
        return [
            {
                'org': 'UserPartitionTransformer',
                'course': 'UP101F',
                'run': 'test_run',
                'user_partitions': [self.user_partition],
                '#type': 'course',
                '#ref': 'course',
                '#children': [
                    {
                        '#type': 'vertical',
                        '#ref': 'A',
                        'metadata': {'group_access': {self.user_partition.id: [0, 1, 2, 3]}},
                    },
                    {'#type': 'vertical', '#ref': 'B'},
                ],
            },
            {
                '#type': 'vertical',
                '#ref': 'C',
                '#parents': ['A'],
                'metadata': {'group_access': {self.user_partition.id: [1, 2]}},
                '#children': [
                    {'#type': 'vertical', '#ref': 'F'},
                    {
                        '#type': 'vertical',
                        '#ref': 'G',
                        'metadata': {'group_access': {self.user_partition.id: [1]}},
                    },
                    {
                        '#type': 'vertical',
                        '#ref': 'H',
                        'metadata': {'group_access': {self.user_partition.id: [2]}},
                    },
                ],
            },
            {
                '#type': 'vertical',
                '#ref': 'D',
                '#parents': ['A'],
                'metadata': {'group_access': {self.user_partition.id: [2, 3]}},
                '#children': [{'#type': 'vertical', '#ref': 'I'}],
            },
            {
                '#type': 'vertical',
                '#ref': 'E',
                '#parents': ['A'],
                '#children': [{'#type': 'vertical', '#ref': 'J'}],
            },
            {
                '#type': 'vertical',
                '#ref': 'K',
                '#parents': ['E'],
                'metadata': {'group_access': {self.user_partition.id: [4]}},
                '#children': [{'#type': 'vertical', '#ref': 'N'}],
            },
            {
                '#type': 'vertical',
                '#ref': 'L',
                '#parents': ['G'],
                'metadata': {'group_access': {self.user_partition.id: [1, 2]}},
            },
            {
                '#type': 'vertical',
                '#ref': 'M',
                '#parents': ['G', 'H'],
                'metadata': {'group_access': {self.user_partition.id: [1, 2, 3]}},
            },
            {
                '#type': 'vertical',
                '#ref': 'O',
                '#parents': ['K', 'B'],
            },
        ]

    @ddt.data(
        (None, ('course', 'B', 'O')),
        (1, ('course', 'A', 'B', 'C', 'E', 'F', 'G', 'J', 'L', 'M', 'O')),
        (2, ('course', 'A', 'B', 'C', 'D', 'E', 'F', 'H', 'I', 'J', 'M', 'O')),
        (3, ('course', 'A', 'B', 'D', 'E', 'I', 'J', 'O')),
        (4, ('course', 'B', 'O')),
    )
    @ddt.unpack
    def test_transform(self, group_id, expected_blocks):
        if group_id:
            add_user_to_cohort(self.cohorts[group_id - 1], self.user.username)

        trans_block_structure = get_course_blocks(
            self.user,
            self.course.location,
            transformers={self.transformer}
        )
        self.assertSetEqual(
            set(trans_block_structure.get_block_keys()),
            self.get_block_key_set(self.blocks, *expected_blocks)
        )


@ddt.ddt
class MergedGroupAccessTestCase(UserPartitionTestMixin, CourseStructureTestCase):
    """
    _MergedGroupAccess Test
    """
    # TODO Test Merged Group Access (MA-1624)

    @ddt.data(
        ([None], None),
        ([{1}, None], {1}),
        ([None, {1}], {1}),
        ([None, {1}, {1, 2}], {1}),
        ([None, {1, 2}, {1, 2}], {1, 2}),
        ([{1, 2, 3}, {1, 2}, None], {1, 2}),
        ([{1, 2}, {1, 2, 3, 4}, None], {1, 2}),
        ([{1}, {2}, None], set()),
        ([None, {1}, {2}, None], set()),
    )
    @ddt.unpack
    def test_intersection_method(self, input_value, expected_result):
        self.assertEquals(
            _MergedGroupAccess._intersection(*input_value),
            expected_result,
        )
