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

from course_blocks.transformers.user_partitions import UserPartitionTransformer
from course_blocks.api import get_course_blocks
from lms.djangoapps.course_blocks.transformers.tests.test_helpers import CourseStructureTestCase


@ddt.ddt
class UserPartitionTransformerTestCase(CourseStructureTestCase):
    """
    UserPartitionTransformer Test
    """
    TEST_PARTITION_ID = 0

    def setUp(self):
        """
        Setup course structure and create user for user partition transformer test.
        """
        super(UserPartitionTransformerTestCase, self).setUp()

        # Set up user partitions and groups.
        self.groups = [Group(1, 'Group 1'), Group(2, 'Group 2'), Group(3, 'Group 3'), Group(4, 'Group 4')]
        self.user_partition = UserPartition(
            id=self.TEST_PARTITION_ID,
            name='Partition 1',
            description='This is partition 1',
            groups=self.groups,
            scheme=CohortPartitionScheme
        )
        self.user_partition.scheme.name = "cohort"

        # Build course.
        self.course_hierarchy = self.get_course_hierarchy()
        self.blocks = self.build_course(self.course_hierarchy)
        self.course = self.blocks['course']

        # Enroll user in course.
        CourseEnrollmentFactory.create(user=self.user, course_id=self.course.id, is_active=True)

        # Set up cohorts.
        config_course_cohorts(self.course, is_cohorted=True)
        self.cohorts = []
        for group in self.groups:
            cohort = CohortFactory(course_id=self.course.id)
            self.cohorts.append(cohort)
            link_cohort_to_partition_group(
                cohort,
                self.user_partition.id,
                group.id,
            )

        self.transformer = UserPartitionTransformer()

    def get_course_hierarchy(self):
        """
        Get a course hierarchy to test with.

        Assumes self.user_partition has already been initialized.
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
                        'metadata': {'group_access': {self.TEST_PARTITION_ID: [0, 1, 2, 3]}},
                    },
                    {'#type': 'vertical', '#ref': 'B'},
                ],
            },
            {
                '#type': 'vertical',
                '#ref': 'C',
                '#parents': ['A'],
                'metadata': {'group_access': {self.TEST_PARTITION_ID: [1, 2]}},
                '#children': [
                    {'#type': 'vertical', '#ref': 'F'},
                    {
                        '#type': 'vertical',
                        '#ref': 'G',
                        'metadata': {'group_access': {self.TEST_PARTITION_ID: [1]}},
                    },
                    {
                        '#type': 'vertical',
                        '#ref': 'H',
                        'metadata': {'group_access': {self.TEST_PARTITION_ID: [2]}},
                    },
                ],
            },
            {
                '#type': 'vertical',
                '#ref': 'D',
                '#parents': ['A'],
                'metadata': {'group_access': {self.TEST_PARTITION_ID: [2, 3]}},
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
                'metadata': {'group_access': {self.TEST_PARTITION_ID: [4]}},
                '#children': [{'#type': 'vertical', '#ref': 'N'}],
            },
            {
                '#type': 'vertical',
                '#ref': 'L',
                '#parents': ['G'],
                'metadata': {'group_access': {self.TEST_PARTITION_ID: [1, 2]}},
            },
            {
                '#type': 'vertical',
                '#ref': 'M',
                '#parents': ['G', 'H'],
                'metadata': {'group_access': {self.TEST_PARTITION_ID: [1, 2, 3]}},
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
    def test_user_assigned(self, group_id, expected_blocks):
        """
        Test when user is assigned to group in user partition.
        """
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

    def test_staff_user(self):
        self.assert_staff_access_to_all_blocks(self.course, self.blocks, self.transformer)
