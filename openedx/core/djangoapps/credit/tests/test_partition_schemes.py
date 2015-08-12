# -*- coding: utf-8 -*-
"""
Tests for In-Course Reverification Access Control Partition scheme
"""

import ddt
import unittest

from django.test import TestCase

from lms.djangoapps.verify_student.models import (
    VerificationCheckpoint,
    VerificationStatus,
    SkippedReverification,
)
from student.models import CourseEnrollment
from xmodule.partitions.partitions import Group, UserPartition, UserPartitionError

from django.conf import settings
from xmodule.modulestore.django import modulestore
from xmodule.modulestore import ModuleStoreEnum
from openedx.core.djangoapps.credit.partition_schemes import VerificationPartitionScheme
from openedx.core.djangoapps.credit.signals import tag_course_content_with_partition_scheme, on_course_publish
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory


@ddt.ddt
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class ReverificationPartitionTest(ModuleStoreTestCase):
    """Tests for the Reverification Partition Scheme. """

    SUBMITTED = "submitted"
    APPROVED = "approved"
    DENIED = "denied"

    NON_VERIFIED_GROUP = Group(
        VerificationPartitionScheme.NON_VERIFIED,
        'Not enrolled in a verified track'
    )

    VERIFIED_ALLOW_GROUP = Group(
        VerificationPartitionScheme.VERIFIED_ALLOW,
        'Enrolled in a verified track and has access'
    )

    VERIFIED_DENY_GROUP = Group(
        VerificationPartitionScheme.VERIFIED_DENY,
        'Enrolled in a verified track and does not have access'
    )

    group_configuration_groups = [
        NON_VERIFIED_GROUP,
        VERIFIED_ALLOW_GROUP,
        VERIFIED_DENY_GROUP,
    ]

    def setUp(self):
        super(ReverificationPartitionTest, self).setUp()

        # creating course, checkpoint location and user partition mock object.
        self.course = CourseFactory.create()
        self.checkpoint_location = u'i4x://{org}/{course}/edx-reverification-block/first_uuid'.format(
            org=self.course.id.org, course=self.course.id.course
        )

        user_partition = UserPartition.get_scheme('verification')
        group_configuration_parameters = {'location': unicode(self.checkpoint_location)}

        self.verification_partition_configuration = UserPartition(
            id=0,
            name='Verification Checkpoint',
            description='verification',
            groups=self.group_configuration_groups,
            scheme=user_partition,
            parameters=group_configuration_parameters,
        )

        self.first_checkpoint = VerificationCheckpoint.objects.create(
            course_id=self.course.id,
            checkpoint_location=self.checkpoint_location
        )

    def created_user_and_enroll(self, enrollment_type):
        """Create and enroll users with provided enrollment type."""

        user = UserFactory.create()
        CourseEnrollment.objects.create(
            user=user,
            course_id=self.course.id,
            mode=enrollment_type,
            is_active=True
        )
        return user

    def add_verification_status(self, user, status):
        """Adding the verification status for a user."""

        VerificationStatus.add_status_from_checkpoints(
            checkpoints=[self.first_checkpoint],
            user=user,
            status=status
        )

    @ddt.data(
        ("verified", SUBMITTED),
        ("verified", APPROVED),
        ("verified", DENIED),
        ("verified", None),
        ("honor", False),
    )
    @ddt.unpack
    def test_get_group_for_user(self, enrollment_type, verification_status):
        # creating user and enroll them.
        user = self.created_user_and_enroll(enrollment_type)
        if verification_status:
            self.add_verification_status(user, verification_status)

        if enrollment_type == 'honor':
            self.assertEqual(
                self.NON_VERIFIED_GROUP,
                VerificationPartitionScheme.get_group_for_user(
                    self.course.id,
                    user,
                    self.verification_partition_configuration
                )
            )

        elif (
                verification_status in [
                    self.SUBMITTED,
                    self.APPROVED,
                    self.DENIED
                ]
                and enrollment_type == 'verified'
        ):
            self.assertEqual(
                self.VERIFIED_ALLOW_GROUP,
                VerificationPartitionScheme.get_group_for_user(
                    self.course.id,
                    user,
                    self.verification_partition_configuration
                )
            )

        else:
            self.assertEqual(
                self.VERIFIED_DENY_GROUP,
                VerificationPartitionScheme.get_group_for_user(
                    self.course.id,
                    user,
                    self.verification_partition_configuration
                )
            )

    def test_get_group_for_user_with_skipped(self):
        # Check that a user is in verified allow group if that user has skipped
        # any ICRV block.
        user = self.created_user_and_enroll('verified')

        SkippedReverification.add_skipped_reverification_attempt(
            checkpoint=self.first_checkpoint,
            user_id=user.id,
            course_id=self.course.id
        )

        self.assertEqual(
            self.VERIFIED_ALLOW_GROUP,
            VerificationPartitionScheme.get_group_for_user(
                self.course.id,
                user,
                self.verification_partition_configuration
            )
        )

    def test_key_for_partition(self):
        # Test that 'key_for_partition' method of partition scheme
        # 'VerificationPartitionScheme' returns desired format for
        # partition id.

        self.assertEqual(
            'verification:{}'.format(
                self.checkpoint_location
            ),
            VerificationPartitionScheme.key_for_partition(
                self.checkpoint_location
            )
        )


class TestExtension(TestCase):
    """ Ensure that the scheme extension is correctly plugged in (via entry
    point in setup.py)
    """

    def test_get_scheme(self):
        # test that 'VerificationPartitionScheme' is present
        self.assertEqual(UserPartition.get_scheme('verification'), VerificationPartitionScheme)

        # now test that exception is raised if we try to access a non existing
        # user partition scheme
        with self.assertRaisesRegexp(UserPartitionError, 'Unrecognized scheme'):
            UserPartition.get_scheme('other')


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class TestCourseTaggingWithVerPartitions(ModuleStoreTestCase):
    """
    Test the tagging of the course tree with user partitions.
    """

    def _add_icrv_with_gated_contents(self, parent, gated_content_parent, counter):
        self.icrv_x_block = ItemFactory.create(
            parent=parent, category='edx-reverification-block', display_name='Test Unit X Block 1'
        )

        self.gated_vertical = ItemFactory.create(
            parent=gated_content_parent,
            category='vertical',
            display_name='Vertical with gated contents %s'.format(
                counter
            )
        )
        self.gated_problem1 = ItemFactory.create(
            parent=self.gated_vertical,
            category='problem',
            display_name='Problem  %s'.format(counter)
        )
        self.gated_problem2 = ItemFactory.create(
            parent=self.gated_vertical,
            category='problem',
            display_name='Problem  %s'.format(counter)
        )

    def setUp(self):
        super(TestCourseTaggingWithVerPartitions, self).setUp()
        self.user = UserFactory.create()
        # Create the course
        self.course = CourseFactory.create(org="MIT", course="DemoX", run="CS101")

        self.section_alone = ItemFactory.create(parent=self.course, category='chapter', display_name='Test Alone Section')

        self.section_with_tree = ItemFactory.create(parent=self.course, category='chapter', display_name='Test Section Tree')

        self.subsection_alone = ItemFactory.create(parent=self.section_with_tree, category='sequential', display_name='Test Subsection No Tree')

        self.subsection_with_tree = ItemFactory.create(parent=self.section_with_tree, category='sequential', display_name='Test Subsection With Tree')

        self.icrv_parent_vertical = ItemFactory.create(parent=self.subsection_with_tree, category='vertical', display_name='Test Unit X Block Parent')

        self.icrv_x_block = ItemFactory.create(
            parent=self.icrv_parent_vertical, category='edx-reverification-block', display_name='Test Unit X Block 1'
        )

        self.gated_vertical = ItemFactory.create(
            parent=self.subsection_with_tree,
            category='vertical',
            display_name='Vertical with gated contents 1'
        )
        self.gated_problem1 = ItemFactory.create(
            parent=self.gated_vertical,
            category='problem',
            display_name='Problem 1'
        )
        self.gated_problem2 = ItemFactory.create(
            parent=self.gated_vertical,
            category='problem',
            display_name='Problem 1'
        )

    def test_tagging_content_single_icrv(self):
        # tag_course_content_with_partition_scheme(self.course.id, partition_scheme='verification')
        on_course_publish(self.course.id)
        course = modulestore().get_course(self.course.id)

        course_user_partitions = course.user_partitions

        section_alone = modulestore().get_item(self.section_alone.location)

        section_with_tree = modulestore().get_item(self.section_with_tree.location)
        subsection_with_tree = modulestore().get_item(self.subsection_with_tree.location)
        icrv_parent_vertical = modulestore().get_item(self.icrv_parent_vertical.location)
        icrv_x_block = modulestore().get_item(self.icrv_x_block.location)

        subsection_alone = modulestore().get_item(self.subsection_alone.location)

        gated_vertical = modulestore().get_item(self.gated_vertical.location)
        gated_problem1 = modulestore().get_item(self.gated_problem1.location)
        gated_problem2 = modulestore().get_item(self.gated_problem2.location)

        # Assert course has one partition and has three verification groups
        self.assertEqual(len(course_user_partitions), 1)
        self.assertEqual(len(course_user_partitions[0].groups), 3)
        partition_groups = [
            VerificationPartitionScheme.VERIFIED_ALLOW,
            VerificationPartitionScheme.VERIFIED_DENY,
            VerificationPartitionScheme.NON_VERIFIED
        ]
        course_user_partitions_groups = [
            group.id for group in course_user_partitions[0].groups
        ]
        self.assertTrue(set(course_user_partitions_groups) == set(partition_groups))

        # Assert subsection with no child don't have any access group
        self.assertTrue(section_alone.group_access == {})
        self.assertTrue(section_with_tree.group_access == {})
        self.assertTrue(subsection_alone.group_access == {})

        # Subsection grand parent of xblock
        self.assertTrue(subsection_with_tree.group_access == {})

        # Vertical parent of xblock
        self.assertTrue(icrv_parent_vertical.group_access == {})

        # Assert icrv xblock has 2 access groups
        icrv_xblock_groups = [VerificationPartitionScheme.VERIFIED_ALLOW, VerificationPartitionScheme.VERIFIED_DENY]
        access_groups_of_verification_partition = self._get_access_groups_of_verification_partition(icrv_x_block)
        self.assertEqual(len(access_groups_of_verification_partition), 2)
        self.assertTrue(set(access_groups_of_verification_partition) == set(icrv_xblock_groups))

        # Gated/ Siblings of ICRV Vertical or problems
        gated_vertical_groups = [VerificationPartitionScheme.NON_VERIFIED, VerificationPartitionScheme.VERIFIED_ALLOW]
        access_groups_of_verification_partition = self._get_access_groups_of_verification_partition(gated_vertical)
        self.assertEqual(len(access_groups_of_verification_partition), 2)
        self.assertTrue(set(access_groups_of_verification_partition) == set(gated_vertical_groups))

        access_groups_of_verification_partition = self._get_access_groups_of_verification_partition(gated_problem1)
        self.assertEqual(len(access_groups_of_verification_partition), 2)
        self.assertTrue(set(access_groups_of_verification_partition) == set(gated_vertical_groups))

        access_groups_of_verification_partition = self._get_access_groups_of_verification_partition(gated_problem2)
        self.assertEqual(len(access_groups_of_verification_partition), 2)
        self.assertTrue(set(access_groups_of_verification_partition) == set(gated_vertical_groups))

    def test_tagging_content_multiple_icrv(self):
        self.section_with_tree2 = ItemFactory.create(
            parent=self.course, category='chapter', display_name='Test Section Tree 2'
        )
        self.subsection_alone2 = ItemFactory.create(
            parent=self.section_with_tree2, category='sequential', display_name='Test Subsection No Tree2'
        )
        self.icrv_parent_subsec2 = ItemFactory.create(
            parent=self.section_with_tree2, category='sequential', display_name='Test Subsection No Tree parent 2'
        )

        self.icrv_x_block2 = ItemFactory.create(
            parent=self.icrv_parent_subsec2,
            category='edx-reverification-block',
            display_name='Test Unit X Block 2'
        )

        self.gated_vertical2 = ItemFactory.create(
            parent=self.icrv_parent_subsec2,
            category='vertical',
            display_name='Vertical with gated contents 2'
        )
        self.gated_problem21 = ItemFactory.create(
            parent=self.gated_vertical2,
            category='problem',
            display_name='Problem 21'
        )
        self.gated_problem22 = ItemFactory.create(
            parent=self.gated_vertical2,
            category='problem',
            display_name='Problem 22'
        )

        # tag_course_content_with_partition_scheme(self.course.id, partition_scheme='verification')
        on_course_publish(self.course.id)
        course = modulestore().get_course(self.course.id)

        course_user_partitions = course.user_partitions

        section_alone = modulestore().get_item(self.section_alone.location)

        section_with_tree = modulestore().get_item(self.section_with_tree.location)
        subsection_with_tree = modulestore().get_item(self.subsection_with_tree.location)
        icrv_parent_vertical = modulestore().get_item(self.icrv_parent_vertical.location)
        icrv_x_block = modulestore().get_item(self.icrv_x_block.location)

        subsection_alone = modulestore().get_item(self.subsection_alone.location)

        gated_vertical = modulestore().get_item(self.gated_vertical.location)
        gated_problem1 = modulestore().get_item(self.gated_problem1.location)
        gated_problem2 = modulestore().get_item(self.gated_problem2.location)

        # Assert course has one partition and has three verification groups
        self.assertEqual(len(course_user_partitions), 2)
        self.assertEqual(len(course_user_partitions[0].groups), 3)
        self.assertEqual(len(course_user_partitions[1].groups), 3)

        partition_groups = [
            VerificationPartitionScheme.VERIFIED_ALLOW,
            VerificationPartitionScheme.VERIFIED_DENY,
            VerificationPartitionScheme.NON_VERIFIED
        ]
        course_user_partitions_groups = [
            group.id for group in course_user_partitions[0].groups
        ]
        self.assertTrue(set(course_user_partitions_groups) == set(partition_groups))

        # Assert subsection with no child don't have any access group
        self.assertTrue(section_alone.group_access == {})
        self.assertTrue(section_with_tree.group_access == {})
        self.assertTrue(subsection_alone.group_access == {})

        # Subsection grand parent of xblock
        self.assertTrue(subsection_alone.group_access == {})
        self.assertTrue(subsection_with_tree.group_access == {})
        self.assertTrue(icrv_parent_vertical.group_access == {})

        icrv_xblock_groups = [VerificationPartitionScheme.VERIFIED_ALLOW, VerificationPartitionScheme.VERIFIED_DENY]
        self._assert_partitions(icrv_x_block, icrv_xblock_groups)

        gated_contents_group_access = [VerificationPartitionScheme.NON_VERIFIED, VerificationPartitionScheme.VERIFIED_ALLOW]
        self._assert_partitions(gated_vertical, gated_contents_group_access)

        self._assert_partitions(gated_problem1, gated_contents_group_access)

        self._assert_partitions(gated_problem2, gated_contents_group_access)

        section_with_tree2 = modulestore().get_item(self.section_with_tree2.location)
        icrv_parent_subsec2 = modulestore().get_item(self.icrv_parent_subsec2.location)
        icrv_x_block2 = modulestore().get_item(self.icrv_x_block2.location)

        subsection_alone2 = modulestore().get_item(self.subsection_alone2.location)

        gated_vertical2 = modulestore().get_item(self.gated_vertical2.location)
        gated_problem21 = modulestore().get_item(self.gated_problem21.location)
        gated_problem22 = modulestore().get_item(self.gated_problem22.location)

        # Assert subsection with no child don't have any access group
        self.assertTrue(section_with_tree2.group_access == {})
        self.assertTrue(subsection_alone2.group_access == {})
        self.assertTrue(icrv_parent_subsec2.group_access == {})

        self._assert_partitions(icrv_x_block2, icrv_xblock_groups)
        self._assert_partitions(gated_vertical2, gated_contents_group_access)
        self._assert_partitions(gated_problem21, gated_contents_group_access)
        self._assert_partitions(gated_problem22, gated_contents_group_access)

    def test_tagging_content_multiple_icrv_delete_icrv(self):
        self.section_with_tree2 = ItemFactory.create(
            parent=self.course, category='chapter', display_name='Test Section Tree 2'
        )
        self.subsection_alone2 = ItemFactory.create(
            parent=self.section_with_tree2, category='sequential', display_name='Test Subsection No Tree2'
        )
        self.icrv_parent_subsec2 = ItemFactory.create(
            parent=self.section_with_tree2, category='sequential', display_name='Test Subsection No Tree parent 2'
        )

        self.icrv_x_block2 = ItemFactory.create(
            parent=self.icrv_parent_subsec2,
            category='edx-reverification-block',
            display_name='Test Unit X Block 2'
        )

        self.gated_vertical2 = ItemFactory.create(
            parent=self.icrv_parent_subsec2,
            category='vertical',
            display_name='Vertical with gated contents 2'
        )
        self.gated_problem21 = ItemFactory.create(
            parent=self.gated_vertical2,
            category='problem',
            display_name='Problem 21'
        )
        self.gated_problem22 = ItemFactory.create(
            parent=self.gated_vertical2,
            category='problem',
            display_name='Problem 22'
        )

        # tag_course_content_with_partition_scheme(self.course.id, partition_scheme='verification')
        on_course_publish(self.course.id)
        course = modulestore().get_course(self.course.id)

        course_user_partitions = course.user_partitions

        section_alone = modulestore().get_item(self.section_alone.location)

        section_with_tree = modulestore().get_item(self.section_with_tree.location)
        subsection_with_tree = modulestore().get_item(self.subsection_with_tree.location)
        icrv_parent_vertical = modulestore().get_item(self.icrv_parent_vertical.location)
        icrv_x_block = modulestore().get_item(self.icrv_x_block.location)

        subsection_alone = modulestore().get_item(self.subsection_alone.location)

        gated_vertical = modulestore().get_item(self.gated_vertical.location)
        gated_problem1 = modulestore().get_item(self.gated_problem1.location)
        gated_problem2 = modulestore().get_item(self.gated_problem2.location)

        # Assert course has one partition and has three verification groups
        self.assertEqual(len(course_user_partitions), 2)
        self.assertEqual(len(course_user_partitions[0].groups), 3)
        self.assertEqual(len(course_user_partitions[1].groups), 3)

        partition_groups = [
            VerificationPartitionScheme.VERIFIED_ALLOW,
            VerificationPartitionScheme.VERIFIED_DENY,
            VerificationPartitionScheme.NON_VERIFIED
        ]
        course_user_partitions_groups = [
            group.id for group in course_user_partitions[0].groups
        ]
        self.assertTrue(set(course_user_partitions_groups) == set(partition_groups))

        # Assert subsection with no child don't have any access group
        self.assertTrue(section_alone.group_access == {})
        self.assertTrue(section_with_tree.group_access == {})
        self.assertTrue(subsection_alone.group_access == {})

        # Subsection grand parent of xblock
        self.assertTrue(subsection_alone.group_access == {})
        self.assertTrue(subsection_with_tree.group_access == {})
        self.assertTrue(icrv_parent_vertical.group_access == {})

        icrv_xblock_groups = [VerificationPartitionScheme.VERIFIED_ALLOW, VerificationPartitionScheme.VERIFIED_DENY]
        self._assert_partitions(icrv_x_block, icrv_xblock_groups)

        gated_contents_group_access = [VerificationPartitionScheme.NON_VERIFIED, VerificationPartitionScheme.VERIFIED_ALLOW]
        self._assert_partitions(gated_vertical, gated_contents_group_access)

        self._assert_partitions(gated_problem1, gated_contents_group_access)

        self._assert_partitions(gated_problem2, gated_contents_group_access)

        section_with_tree2 = modulestore().get_item(self.section_with_tree2.location)
        icrv_parent_subsec2 = modulestore().get_item(self.icrv_parent_subsec2.location)
        icrv_x_block2 = modulestore().get_item(self.icrv_x_block2.location)

        subsection_alone2 = modulestore().get_item(self.subsection_alone2.location)

        gated_vertical2 = modulestore().get_item(self.gated_vertical2.location)
        gated_problem21 = modulestore().get_item(self.gated_problem21.location)
        gated_problem22 = modulestore().get_item(self.gated_problem22.location)

        # Assert subsection with no child don't have any access group
        self.assertTrue(section_with_tree2.group_access == {})
        self.assertTrue(subsection_alone2.group_access == {})
        self.assertTrue(icrv_parent_subsec2.group_access == {})

        self._assert_partitions(icrv_x_block2, icrv_xblock_groups)
        self._assert_partitions(gated_vertical2, gated_contents_group_access)
        self._assert_partitions(gated_problem21, gated_contents_group_access)
        self._assert_partitions(gated_problem22, gated_contents_group_access)

        # Delete the first ICRV block
        with modulestore().branch_setting(ModuleStoreEnum.Branch.draft_preferred, self.course.id):
            modulestore().delete_item(self.icrv_x_block.location, self.user.id)

        with modulestore().branch_setting(ModuleStoreEnum.Branch.draft_preferred):
            modulestore().publish(self.icrv_parent_vertical.location, ModuleStoreEnum.UserID.test)

        tag_course_content_with_partition_scheme(self.course.id, partition_scheme='verification')

        section_with_tree2 = modulestore().get_item(self.section_with_tree2.location)
        icrv_parent_subsec2 = modulestore().get_item(self.icrv_parent_subsec2.location)
        icrv_x_block2 = modulestore().get_item(self.icrv_x_block2.location)

        subsection_alone2 = modulestore().get_item(self.subsection_alone2.location)

        gated_vertical2 = modulestore().get_item(self.gated_vertical2.location)
        gated_problem21 = modulestore().get_item(self.gated_problem21.location)
        gated_problem22 = modulestore().get_item(self.gated_problem22.location)

        # Assert subsection with no child don't have any access group
        self.assertTrue(section_with_tree2.group_access == {})
        self.assertTrue(subsection_alone2.group_access == {})
        self.assertTrue(icrv_parent_subsec2.group_access == {})

        self._assert_partitions(icrv_x_block2, icrv_xblock_groups)
        self._assert_partitions(gated_vertical2, gated_contents_group_access)
        self._assert_partitions(gated_problem21, gated_contents_group_access)
        self._assert_partitions(gated_problem22, gated_contents_group_access)

        self._assert_icrv_subtree()

    def _get_access_groups_of_verification_partition(self, xblock):
        group_access = []
        for partition_id, group_access in xblock.group_access.items():
            verification_partition = self._get_verification_partition_from_xblock(partition_id, xblock)
            if verification_partition:
                return group_access
        return group_access

    def _get_verification_partition_from_xblock(self, partition_id, xblock):
        for partition in xblock.user_partitions:
            if partition.id == partition_id and partition.scheme == VerificationPartitionScheme:
                return partition

    def _assert_partitions(self, xblock, expected_group_access):
        access_groups_of_verification_partition = self._get_access_groups_of_verification_partition(xblock)
        self.assertEqual(len(access_groups_of_verification_partition), 2)
        self.assertTrue(set(access_groups_of_verification_partition) == set(expected_group_access))

    def _assert_icrv_subtree(self):
        course = modulestore().get_course(self.course.id)

        course_user_partitions = course.user_partitions
        section_alone = modulestore().get_item(self.section_alone.location)

        section_with_tree = modulestore().get_item(self.section_with_tree.location)
        subsection_with_tree = modulestore().get_item(self.subsection_with_tree.location)
        icrv_parent_vertical = modulestore().get_item(self.icrv_parent_vertical.location)

        subsection_alone = modulestore().get_item(self.subsection_alone.location)

        gated_vertical = modulestore().get_item(self.gated_vertical.location)
        gated_problem1 = modulestore().get_item(self.gated_problem1.location)
        gated_problem2 = modulestore().get_item(self.gated_problem2.location)

        # Assert course has one partition and has three verification groups
        self.assertEqual(len(course_user_partitions), 1)
        self.assertEqual(len(course_user_partitions[0].groups), 3)

        partition_groups = [
            VerificationPartitionScheme.VERIFIED_ALLOW,
            VerificationPartitionScheme.VERIFIED_DENY,
            VerificationPartitionScheme.NON_VERIFIED
        ]
        course_user_partitions_groups = [
            group.id for group in course_user_partitions[0].groups
        ]
        self.assertTrue(set(course_user_partitions_groups) == set(partition_groups))

        # Assert subsection with no child don't have any access group
        self.assertTrue(section_alone.group_access == {})
        self.assertTrue(section_with_tree.group_access == {})
        self.assertTrue(subsection_alone.group_access == {})

        # Subsection grand parent of xblock
        self.assertTrue(subsection_alone.group_access == {})
        self.assertTrue(subsection_with_tree.group_access == {})
        self.assertTrue(icrv_parent_vertical.group_access == {})

        self.assertTrue(gated_vertical.group_access == {})
        self.assertTrue(gated_problem1.group_access == {})
        self.assertTrue(gated_problem2.group_access == {})
