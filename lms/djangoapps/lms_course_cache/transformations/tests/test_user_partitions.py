"""
Tests for UserPartitionTransformation.
"""

from openedx.core.djangoapps.course_groups.partition_scheme import CohortPartitionScheme
from openedx.core.djangoapps.course_groups.tests.helpers import CohortFactory, config_course_cohorts
from openedx.core.djangoapps.course_groups.cohorts import add_user_to_cohort
from openedx.core.djangoapps.course_groups.views import link_cohort_to_partition_group
from student.tests.factories import UserFactory
from student.tests.factories import CourseEnrollmentFactory
from xmodule.modulestore.django import modulestore
from xmodule.partitions.partitions import Group, UserPartition

from lms_course_cache.transformations.user_partitions import UserPartitionTransformation
from lms_course_cache.api import get_course_blocks, clear_course_from_cache
from test_helpers import CourseStructureTestCase


class UserPartitionTransformationTestCase(CourseStructureTestCase):
    """
    ...
    """

    def setUp(self):
        super(UserPartitionTransformationTestCase, self).setUp()

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
        self.add_user_to_cohort_group(0)

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
                            'metadata': {'group_access': {0: [0, 1, 2]},
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

    def add_user_to_cohort_group(self, cohort_index):
        """
        Add user to cohort, link cohort to content group, and update blocks.
        """
        add_user_to_cohort(self.cohorts[cohort_index], self.user.username)
        link_cohort_to_partition_group(
            self.cohorts[cohort_index],
            self.user_partition.id,
            self.groups[cohort_index].id,
        )
        store = modulestore()
        for __, block in self.blocks.iteritems():
            block.save()
            store.update_item(block, self.user.id)

    def get_block_key_set(self, *refs):
        """
        Gets the set of usage keys that correspond to the list of
        #ref values as defined on self.blocks.

        Returns: set[UsageKey]
        """
        xblocks = (self.blocks[ref] for ref in refs)
        return set([xblock.location for xblock in xblocks])

    def test_course_structure_with_user_partition_enrolled(self):
        self.transformation = UserPartitionTransformation()

        __, raw_data_blocks = get_course_blocks(
            self.user,
            self.course.id,
            transformations={}
        )
        self.assertEqual(len(raw_data_blocks), len(self.blocks))

        clear_course_from_cache(self.course.id)
        __, trans_data_blocks = get_course_blocks(
            self.user,
            self.course.id,
            transformations={self.transformation}
        )
        self.assertEqual(
            set(trans_data_blocks.keys()),
            self.get_block_key_set('course', 'chapter1', 'lesson1', 'vertical1', 'html2')
        )
