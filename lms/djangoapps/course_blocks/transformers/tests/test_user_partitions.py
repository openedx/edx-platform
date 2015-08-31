"""
Tests for UserPartitionTransformer.
"""

from openedx.core.djangoapps.course_groups.partition_scheme import CohortPartitionScheme
from openedx.core.djangoapps.course_groups.tests.helpers import CohortFactory, config_course_cohorts
from openedx.core.djangoapps.course_groups.cohorts import add_user_to_cohort
from openedx.core.djangoapps.course_groups.views import link_cohort_to_partition_group
from student.tests.factories import UserFactory
from student.tests.factories import CourseEnrollmentFactory
from xmodule.partitions.partitions import Group, UserPartition

from course_blocks.transformers.user_partitions import UserPartitionTransformer
from course_blocks.api import get_course_blocks, clear_course_from_cache
from lms.djangoapps.course_blocks.transformers.tests.test_helpers import CourseStructureTestCase


class UserPartitionTransformerTestCase(CourseStructureTestCase):
    """
    UserPartitionTransformer Test
    """
    def setUp(self):
        """
        Setup course structure and create user for user partition transformer test.
        """
        super(UserPartitionTransformerTestCase, self).setUp()

        # Set up user partitions and groups.
        self.groups = [Group(1, 'Group 1'), Group(2, 'Group 2')]
        self.content_groups = [1, 2]
        self.user_partition = UserPartition(
            id=0,
            name='Partition 1',
            description='This is partition 1',
            groups=self.groups,
            scheme=CohortPartitionScheme
        )
        self.user_partition.scheme.name = "cohort"

        # Build course.
        self.course_hierarchy = self.get_test_course_hierarchy()
        self.blocks = self.build_course(self.course_hierarchy)
        self.course = self.blocks['course']
        clear_course_from_cache(self.course.id)

        # Set up user and enroll in course.
        self.password = 'test'
        self.user = UserFactory.create(password=self.password)
        CourseEnrollmentFactory.create(user=self.user, course_id=self.course.id, is_active=True)

        # Set up cohorts.
        config_course_cohorts(self.course, is_cohorted=True)
        self.cohorts = [CohortFactory(course_id=self.course.id) for __ in enumerate(self.groups)]
        self.add_user_to_cohort_group(self.cohorts[0], self.groups[0])

    def get_test_course_hierarchy(self):
        """
        Get a course hierarchy to test with.

        Assumes self.user_partition has already been initialized.
        """
        return {
            'org': 'UserPartitionTransformation',
            'course': 'UP101F',
            'run': 'test_run',
            'user_partitions': [self.user_partition],
            '#ref': 'course',
            '#children': [
                {
                    '#type': 'chapter',
                    '#ref': 'chapter1',
                    '#children': [
                        {
                            'metadata': {
                                'group_access': {0: [0, 1, 2]},
                            },
                            '#type': 'sequential',
                            '#ref': 'lesson1',
                            '#children': [
                                {
                                    '#type': 'vertical',
                                    '#ref': 'vertical1',
                                    '#children': [
                                        {
                                            'metadata': {'group_access': {0: [0]}},
                                            '#type': 'html',
                                            '#ref': 'html1',
                                        },
                                        {
                                            'metadata': {'group_access': {0: [1]}},
                                            '#type': 'html',
                                            '#ref': 'html2',
                                        }
                                    ],
                                }
                            ],
                        }
                    ],
                }
            ]
        }

    def add_user_to_cohort_group(self, cohort, group):
        """
        Add user to cohort, link cohort to content group, and update blocks.
        """
        add_user_to_cohort(cohort, self.user.username)
        link_cohort_to_partition_group(
            cohort,
            self.user_partition.id,
            group.id,
        )

    def test_course_structure_with_user_partition(self):
        """
        Test course structure integrity if course has user partition section
        and user is assigned to group in user partition.
        """
        self.transformation = UserPartitionTransformer()

        raw_block_structure = get_course_blocks(
            self.user,
            self.course.id,
            self.course.location,
            transformers={}
        )
        self.assertEqual(len(list(raw_block_structure.get_block_keys())), len(self.blocks))

        clear_course_from_cache(self.course.id)
        trans_block_structure = get_course_blocks(
            self.user,
            self.course.id,
            self.course.location,
            transformers={self.transformation}
        )
        self.assertSetEqual(
            set(trans_block_structure.get_block_keys()),
            self.get_block_key_set('course', 'chapter1', 'lesson1', 'vertical1', 'html2')
        )
