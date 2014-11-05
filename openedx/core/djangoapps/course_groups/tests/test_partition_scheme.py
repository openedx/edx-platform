"""
Test the partitions and partitions service

"""

from django.conf import settings
import django.test
from django.test.utils import override_settings
from mock import patch

from student.tests.factories import UserFactory
from xmodule.partitions.partitions import Group, UserPartition, UserPartitionError
from xmodule.modulestore.django import modulestore, clear_existing_modulestores
from xmodule.modulestore.tests.django_utils import mixed_store_config
from opaque_keys.edx.locations import SlashSeparatedCourseKey

from ..partition_scheme import CohortPartitionScheme
from ..models import CourseUserGroupPartitionGroup
from ..cohorts import add_user_to_cohort
from .helpers import CohortFactory, config_course_cohorts


TEST_DATA_DIR = settings.COMMON_TEST_DATA_ROOT
TEST_MAPPING = {'edX/toy/2012_Fall': 'xml'}
TEST_DATA_MIXED_MODULESTORE = mixed_store_config(TEST_DATA_DIR, TEST_MAPPING)


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class TestCohortPartitionScheme(django.test.TestCase):
    """
    Test the logic for linking a user to a partition group based on their cohort.
    """

    def setUp(self):
        """
        Regenerate a course with cohort configuration, partition and groups,
        and a student for each test.
        """
        self.course_key = SlashSeparatedCourseKey("edX", "toy", "2012_Fall")
        config_course_cohorts(modulestore().get_course(self.course_key), [], cohorted=True)

        self.groups = [Group(10, 'Group 10'), Group(20, 'Group 20')]
        self.user_partition = UserPartition(
            0,
            'Test Partition',
            'for testing purposes',
            self.groups,
            scheme=CohortPartitionScheme
        )
        self.student = UserFactory.create()

    def link_cohort_partition_group(self, cohort, partition, group):
        """
        Utility for creating cohort -> partition group links
        """
        CourseUserGroupPartitionGroup(
            course_user_group=cohort,
            partition_id=partition.id,
            group_id=group.id,
        ).save()

    def unlink_cohort_partition_group(self, cohort):
        """
        Utility for removing cohort -> partition group links
        """
        CourseUserGroupPartitionGroup.objects.filter(course_user_group=cohort).delete()

    def assert_student_in_group(self, group, partition=None):
        """
        Utility for checking that our test student comes up as assigned to the
        specified partition (or, if None, no partition at all)
        """
        self.assertEqual(
            CohortPartitionScheme.get_group_for_user(
                self.course_key,
                self.student,
                partition or self.user_partition,
            ),
            group
        )

    def test_student_cohort_assignment(self):
        """
        Test that the CohortPartitionScheme continues to return the correct
        group for a student as the student is moved in and out of different
        cohorts.
        """
        first_cohort, second_cohort = [
            CohortFactory(course_id=self.course_key) for _ in range(2)
        ]
        # place student 0 into first cohort
        add_user_to_cohort(first_cohort, self.student.username)
        self.assert_student_in_group(None)

        # link first cohort to group 0 in the partition
        self.link_cohort_partition_group(
            first_cohort,
            self.user_partition,
            self.groups[0],
        )
        # link second cohort to to group 1 in the partition
        self.link_cohort_partition_group(
            second_cohort,
            self.user_partition,
            self.groups[1],
        )
        self.assert_student_in_group(self.groups[0])

        # move student from first cohort to second cohort
        add_user_to_cohort(second_cohort, self.student.username)
        self.assert_student_in_group(self.groups[1])

        # move the student out of the cohort
        second_cohort.users.remove(self.student)
        self.assert_student_in_group(None)

    def test_cohort_partition_group_assignment(self):
        """
        Test that the CohortPartitionScheme returns the correct group for a
        student in a cohort when the cohort link is created / moved / deleted.
        """
        test_cohort = CohortFactory(course_id=self.course_key)

        # assign user to cohort (but cohort isn't linked to a partition group yet)
        add_user_to_cohort(test_cohort, self.student.username)
        # scheme should not yet find any link
        self.assert_student_in_group(None)

        # link cohort to group 0
        self.link_cohort_partition_group(
            test_cohort,
            self.user_partition,
            self.groups[0],
        )
        # now the scheme should find a link
        self.assert_student_in_group(self.groups[0])

        # link cohort to group 1 (first unlink it from group 0)
        self.unlink_cohort_partition_group(test_cohort)
        self.link_cohort_partition_group(
            test_cohort,
            self.user_partition,
            self.groups[1],
        )
        # scheme should pick up the link
        self.assert_student_in_group(self.groups[1])

        # unlink cohort from anywhere
        self.unlink_cohort_partition_group(
            test_cohort,
        )
        # scheme should now return nothing
        self.assert_student_in_group(None)

    def setup_student_in_group_0(self):
        """
        Utility to set up a cohort, add our student to the cohort, and link
        the cohort to self.groups[0]
        """
        test_cohort = CohortFactory(course_id=self.course_key)

        # link cohort to group 0
        self.link_cohort_partition_group(
            test_cohort,
            self.user_partition,
            self.groups[0],
        )
        # place student into cohort
        add_user_to_cohort(test_cohort, self.student.username)
        # check link is correct
        self.assert_student_in_group(self.groups[0])

    def test_partition_changes_nondestructive(self):
        """
        If the name of a user partition is changed, or a group is added to the
        partition, links from cohorts do not break.

        If the name of a group is changed, links from cohorts do not break.
        """
        self.setup_student_in_group_0()

        # to simulate a non-destructive configuration change on the course, create
        # a new partition with the same id and scheme but with groups renamed and
        # a group added
        new_groups = [Group(10, 'New Group 10'), Group(20, 'New Group 20'), Group(30, 'New Group 30')]
        new_user_partition = UserPartition(
            0,  # same id
            'Different Partition',
            'dummy',
            new_groups,
            scheme=CohortPartitionScheme,
        )
        # the link should still work
        self.assert_student_in_group(new_groups[0], new_user_partition)

    def test_missing_group(self):
        """
        If the group is deleted (or its id is changed), there's no referential
        integrity enforced, so any references from cohorts to that group will be
        lost.  A warning should be logged when links are found from cohorts to
        groups that no longer exist.
        """
        self.setup_student_in_group_0()

        # to simulate a destructive change on the course, create a new partition
        # with the same id, but different group ids.
        new_user_partition = UserPartition(
            0,  # same id
            'Another Partition',
            'dummy',
            [Group(11, 'Not Group 10'), Group(21, 'Not Group 20')],  # different ids
            scheme=CohortPartitionScheme,
        )
        # the partition will be found since it has the same id, but the group
        # ids aren't present anymore, so the scheme returns None (and logs a
        # warning)
        with patch('openedx.core.djangoapps.course_groups.partition_scheme.log') as mock_log:
            self.assert_student_in_group(None, new_user_partition)
            self.assertTrue(mock_log.warn.called)
            self.assertRegexpMatches(mock_log.warn.call_args[0][0], 'group not found')

    def test_missing_partition(self):
        """
        If the user partition is deleted (or its id is changed), there's no
        referential integrity enforced, so any references from cohorts to that
        partition's groups will be lost.  A warning should be logged when links
        are found from cohorts to partitions that do not exist.
        """
        self.setup_student_in_group_0()

        # to simulate another destructive change on the course, create a new
        # partition with a different id, but using the same groups.
        new_user_partition = UserPartition(
            1,  # different id
            'Moved Partition',
            'dummy',
            [Group(10, 'Group 10'), Group(20, 'Group 20')],  # same ids
            scheme=CohortPartitionScheme,
        )
        # the partition will not be found even though the group ids match, so the
        # scheme returns None (and logs a warning).
        with patch('openedx.core.djangoapps.course_groups.partition_scheme.log') as mock_log:
            self.assert_student_in_group(None, new_user_partition)
            self.assertTrue(mock_log.warn.called)
            self.assertRegexpMatches(mock_log.warn.call_args[0][0], 'partition mismatch')


class TestExtension(django.test.TestCase):
    """
    Ensure that the scheme extension is correctly plugged in (via entry point
    in setup.py)
    """

    def test_get_scheme(self):
        self.assertEqual(UserPartition.get_scheme('cohort'), CohortPartitionScheme)
        with self.assertRaisesRegexp(UserPartitionError, 'Unrecognized scheme'):
            UserPartition.get_scheme('other')
