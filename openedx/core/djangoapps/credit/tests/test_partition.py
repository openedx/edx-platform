# -*- coding: utf-8 -*-
"""
Tests for In-Course Reverification Access Control Partition scheme
"""

import ddt
import unittest
from mock import Mock

from django.conf import settings

from lms.djangoapps.verify_student.models import (
    VerificationCheckpoint,
    VerificationStatus,
    SkippedReverification,
)
from openedx.core.djangoapps.credit.partition_schemes import VerificationPartitionScheme
from student.models import CourseEnrollment
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


@ddt.ddt
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class ReverificationPartitionTest(ModuleStoreTestCase):
    """Tests for the Reverification Partition Scheme. """

    SUBMITTED = "submitted"
    APPROVED = "approved"
    DENIED = "denied"

    def setUp(self):
        super(ReverificationPartitionTest, self).setUp()

        # creating course, checkpoint location and user partition mock object.
        self.course = CourseFactory.create()
        self.checkpoint_location = u'i4x://{org}/{course}/edx-reverification-block/first_uuid'.format(
            org=self.course.id.org, course=self.course.id.course
        )
        self.user_partition = Mock(user_partitions=[])
        self.user_partition.parameters = {
            "location": self.checkpoint_location
        }

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
        ("verified", SUBMITTED),
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
                VerificationPartitionScheme.NON_VERIFIED,
                VerificationPartitionScheme.get_group_for_user(
                    self.course.id,
                    user,
                    self.user_partition
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
                VerificationPartitionScheme.VERIFIED_ALLOW,
                VerificationPartitionScheme.get_group_for_user(
                    self.course.id,
                    user,
                    self.user_partition
                )
            )

        else:
            self.assertEqual(
                VerificationPartitionScheme.VERIFIED_DENY,
                VerificationPartitionScheme.get_group_for_user(
                    self.course.id,
                    user,
                    self.user_partition
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

    def test_cache_with_skipped_icrv(self):
        # Check that a user is in verified allow group if that user has skipped
        # any ICRV block.
        user = self.created_user_and_enroll('verified')
        SkippedReverification.add_skipped_reverification_attempt(
            checkpoint=self.first_checkpoint,
            user_id=user.id,
            course_id=self.course.id
        )
        # this will warm the cache.
        with self.assertNumQueries(3):
            self.assertEqual(
                VerificationPartitionScheme.VERIFIED_ALLOW,
                VerificationPartitionScheme.get_group_for_user(
                    self.course.id,
                    user,
                    self.user_partition
                )
            )

        # no db queries this time.
        with self.assertNumQueries(0):
            self.assertEqual(
                VerificationPartitionScheme.VERIFIED_ALLOW,
                VerificationPartitionScheme.get_group_for_user(
                    self.course.id,
                    user,
                    self.user_partition
                )
            )

    def test_cache_with_submitted_status(self):
        # Check that a user is in verified allow group if that user has approved status at
        # any ICRV block.
        user = self.created_user_and_enroll('verified')
        self.add_verification_status(user, VerificationStatus.APPROVED_STATUS)
        # this will warm the cache.
        with self.assertNumQueries(4):
            self.assertEqual(
                VerificationPartitionScheme.VERIFIED_ALLOW,
                VerificationPartitionScheme.get_group_for_user(
                    self.course.id,
                    user,
                    self.user_partition
                )
            )

        # no db queries this time.
        with self.assertNumQueries(0):
            self.assertEqual(
                VerificationPartitionScheme.VERIFIED_ALLOW,
                VerificationPartitionScheme.get_group_for_user(
                    self.course.id,
                    user,
                    self.user_partition
                )
            )

    def test_cache_with_denied_status(self):
        # Check that a user is in verified allow group if that user has denied at
        # any ICRV block.
        user = self.created_user_and_enroll('verified')
        self.add_verification_status(user, VerificationStatus.DENIED_STATUS)

        # this will warm the cache.
        with self.assertNumQueries(4):
            self.assertEqual(
                VerificationPartitionScheme.VERIFIED_ALLOW,
                VerificationPartitionScheme.get_group_for_user(
                    self.course.id,
                    user,
                    self.user_partition
                )
            )

        # no db queries this time.
        with self.assertNumQueries(0):
            self.assertEqual(
                VerificationPartitionScheme.VERIFIED_ALLOW,
                VerificationPartitionScheme.get_group_for_user(
                    self.course.id,
                    user,
                    self.user_partition
                )
            )

    def test_cache_with_honor(self):
        # Check that a user is in honor mode.
        # any ICRV block.
        user = self.created_user_and_enroll('honor')
        # this will warm the cache.
        with self.assertNumQueries(3):
            self.assertEqual(
                VerificationPartitionScheme.NON_VERIFIED,
                VerificationPartitionScheme.get_group_for_user(
                    self.course.id,
                    user,
                    self.user_partition
                )
            )

        # no db queries this time.
        with self.assertNumQueries(0):
            self.assertEqual(
                VerificationPartitionScheme.NON_VERIFIED,
                VerificationPartitionScheme.get_group_for_user(
                    self.course.id,
                    user,
                    self.user_partition
                )
            )

    def test_cache_with_verified_deny_group(self):
        # Check that a user is in verified mode. But not perform any action

        user = self.created_user_and_enroll('verified')
        # this will warm the cache.
        with self.assertNumQueries(3):
            self.assertEqual(
                VerificationPartitionScheme.VERIFIED_DENY,
                VerificationPartitionScheme.get_group_for_user(
                    self.course.id,
                    user,
                    self.user_partition
                )
            )

        # no db queries this time.
        with self.assertNumQueries(0):
            self.assertEqual(
                VerificationPartitionScheme.VERIFIED_DENY,
                VerificationPartitionScheme.get_group_for_user(
                    self.course.id,
                    user,
                    self.user_partition
                )
            )
