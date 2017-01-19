# -*- coding: utf-8 -*-
"""
Tests for In-Course Reverification Access Control Partition scheme
"""

import ddt
from nose.plugins.attrib import attr

from lms.djangoapps.verify_student.models import (
    VerificationCheckpoint,
    VerificationStatus,
    SkippedReverification,
)
from openedx.core.djangoapps.credit.partition_schemes import VerificationPartitionScheme
from openedx.core.djangolib.testing.utils import skip_unless_lms
from student.models import CourseEnrollment
from student.tests.factories import UserFactory
from xmodule.partitions.partitions import UserPartition, Group
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


@attr(shard=2)
@ddt.ddt
@skip_unless_lms
class ReverificationPartitionTest(ModuleStoreTestCase):
    """Tests for the Reverification Partition Scheme. """

    SUBMITTED = "submitted"
    APPROVED = "approved"
    DENIED = "denied"
    ENABLED_CACHES = ['default', 'mongo_metadata_inheritance', 'loc_cache']

    def setUp(self):
        super(ReverificationPartitionTest, self).setUp()

        # creating course, checkpoint location and user partition mock object.
        self.course = CourseFactory.create()
        self.checkpoint_location = u'i4x://{org}/{course}/edx-reverification-block/first_uuid'.format(
            org=self.course.id.org, course=self.course.id.course
        )

        scheme = UserPartition.get_scheme("verification")
        self.user_partition = UserPartition(
            id=0,
            name=u"Verification Checkpoint",
            description=u"Verification Checkpoint",
            scheme=scheme,
            parameters={"location": self.checkpoint_location},
            groups=[
                Group(scheme.ALLOW, "Allow access to content"),
                Group(scheme.DENY, "Deny access to content"),
            ]
        )

        self.first_checkpoint = VerificationCheckpoint.objects.create(
            course_id=self.course.id,
            checkpoint_location=self.checkpoint_location
        )

    def create_user_and_enroll(self, enrollment_type):
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
        ("verified", SUBMITTED, VerificationPartitionScheme.ALLOW),
        ("verified", APPROVED, VerificationPartitionScheme.ALLOW),
        ("verified", DENIED, VerificationPartitionScheme.ALLOW),
        ("verified", None, VerificationPartitionScheme.DENY),
        ("honor", None, VerificationPartitionScheme.ALLOW),
    )
    @ddt.unpack
    def test_get_group_for_user(self, enrollment_type, verification_status, expected_group):
        # creating user and enroll them.
        user = self.create_user_and_enroll(enrollment_type)
        if verification_status:
            self.add_verification_status(user, verification_status)

        self._assert_group_assignment(user, expected_group)

    def test_get_group_for_user_with_skipped(self):
        # Check that a user is in verified allow group if that user has skipped
        # any ICRV block.
        user = self.create_user_and_enroll('verified')

        SkippedReverification.add_skipped_reverification_attempt(
            checkpoint=self.first_checkpoint,
            user_id=user.id,
            course_id=self.course.id
        )

        self._assert_group_assignment(user, VerificationPartitionScheme.ALLOW)

    def test_cache_with_skipped_icrv(self):
        # Check that a user is in verified allow group if that user has skipped
        # any ICRV block.
        user = self.create_user_and_enroll('verified')
        SkippedReverification.add_skipped_reverification_attempt(
            checkpoint=self.first_checkpoint,
            user_id=user.id,
            course_id=self.course.id
        )
        # this will warm the cache.
        with self.assertNumQueries(3):
            self._assert_group_assignment(user, VerificationPartitionScheme.ALLOW)

        # no db queries this time.
        with self.assertNumQueries(0):
            self._assert_group_assignment(user, VerificationPartitionScheme.ALLOW)

    def test_cache_with_submitted_status(self):
        # Check that a user is in verified allow group if that user has approved status at
        # any ICRV block.
        user = self.create_user_and_enroll('verified')
        self.add_verification_status(user, VerificationStatus.APPROVED_STATUS)
        # this will warm the cache.
        with self.assertNumQueries(4):
            self._assert_group_assignment(user, VerificationPartitionScheme.ALLOW)

        # no db queries this time.
        with self.assertNumQueries(0):
            self._assert_group_assignment(user, VerificationPartitionScheme.ALLOW)

    def test_cache_with_denied_status(self):
        # Check that a user is in verified allow group if that user has denied at
        # any ICRV block.
        user = self.create_user_and_enroll('verified')
        self.add_verification_status(user, VerificationStatus.DENIED_STATUS)

        # this will warm the cache.
        with self.assertNumQueries(4):
            self._assert_group_assignment(user, VerificationPartitionScheme.ALLOW)

        # no db queries this time.
        with self.assertNumQueries(0):
            self._assert_group_assignment(user, VerificationPartitionScheme.ALLOW)

    def test_cache_with_honor(self):
        # Check that a user is in honor mode.
        # any ICRV block.
        user = self.create_user_and_enroll('honor')
        # this will warm the cache.
        with self.assertNumQueries(3):
            self._assert_group_assignment(user, VerificationPartitionScheme.ALLOW)

        # no db queries this time.
        with self.assertNumQueries(0):
            self._assert_group_assignment(user, VerificationPartitionScheme.ALLOW)

    def test_cache_with_verified_deny_group(self):
        # Check that a user is in verified mode. But not perform any action

        user = self.create_user_and_enroll('verified')
        # this will warm the cache.
        with self.assertNumQueries(3):
            self._assert_group_assignment(user, VerificationPartitionScheme.DENY)

        # no db queries this time.
        with self.assertNumQueries(0):
            self._assert_group_assignment(user, VerificationPartitionScheme.DENY)

    def _assert_group_assignment(self, user, expected_group_id):
        """Check that the user was assigned to a group. """
        actual_group = VerificationPartitionScheme.get_group_for_user(self.course.id, user, self.user_partition)
        self.assertEqual(actual_group.id, expected_group_id)
