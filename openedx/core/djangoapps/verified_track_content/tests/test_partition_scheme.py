"""
Tests for verified_track_content/partition_scheme.py.
"""


from datetime import datetime, timedelta

import pytz
import six

from common.djangoapps.course_modes.models import CourseMode
from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.partitions.partitions import MINIMUM_STATIC_PARTITION_ID, UserPartition, ReadOnlyUserPartitionError

from ..models import VerifiedTrackCohortedCourse
from ..partition_scheme import ENROLLMENT_GROUP_IDS, EnrollmentTrackPartitionScheme, EnrollmentTrackUserPartition


class EnrollmentTrackUserPartitionTest(SharedModuleStoreTestCase):
    """
    Tests for the custom EnrollmentTrackUserPartition (dynamic groups).
    """

    @classmethod
    def setUpClass(cls):
        super(EnrollmentTrackUserPartitionTest, cls).setUpClass()
        cls.course = CourseFactory.create()

    def test_only_default_mode(self):
        partition = create_enrollment_track_partition(self.course)
        groups = partition.groups
        self.assertEqual(1, len(groups))
        self.assertEqual("Audit", groups[0].name)

    def test_using_verified_track_cohort(self):
        VerifiedTrackCohortedCourse.objects.create(course_key=self.course.id, enabled=True).save()
        partition = create_enrollment_track_partition(self.course)
        self.assertEqual(0, len(partition.groups))

    def test_multiple_groups(self):
        create_mode(self.course, CourseMode.AUDIT, "Audit Enrollment Track", min_price=0)
        # Note that the verified mode is expired-- this is intentional.
        create_mode(
            self.course, CourseMode.VERIFIED, "Verified Enrollment Track", min_price=1,
            expiration_datetime=datetime.now(pytz.UTC) + timedelta(days=-1)
        )
        # Note that the credit mode is not selectable-- this is intentional so we
        # can test that it is filtered out.
        create_mode(self.course, CourseMode.CREDIT_MODE, "Credit Mode", min_price=2)

        partition = create_enrollment_track_partition(self.course)
        groups = partition.groups
        self.assertEqual(2, len(groups))
        self.assertIsNotNone(self.get_group_by_name(partition, "Audit Enrollment Track"))
        self.assertIsNotNone(self.get_group_by_name(partition, "Verified Enrollment Track"))

    def test_to_json_supported(self):
        user_partition_json = create_enrollment_track_partition(self.course).to_json()
        self.assertEqual('Test Enrollment Track Partition', user_partition_json['name'])
        self.assertEqual('enrollment_track', user_partition_json['scheme'])
        self.assertEqual('Test partition for segmenting users by enrollment track', user_partition_json['description'])

    def test_from_json_not_supported(self):
        user_partition_json = create_enrollment_track_partition(self.course).to_json()
        with self.assertRaises(ReadOnlyUserPartitionError):
            UserPartition.from_json(user_partition_json)

    def test_group_ids(self):
        """
        Test that group IDs are all less than MINIMUM_STATIC_PARTITION_ID (to avoid overlapping
        with group IDs associated with cohort and random user partitions).
        """
        for mode in ENROLLMENT_GROUP_IDS:
            self.assertLess(ENROLLMENT_GROUP_IDS[mode]['id'], MINIMUM_STATIC_PARTITION_ID)

    @staticmethod
    def get_group_by_name(partition, name):
        """
        Return the group in the EnrollmentTrackUserPartition with the given name.
        If no such group exists, returns `None`.
        """
        for group in partition.groups:
            if group.name == name:
                return group
        return None


class EnrollmentTrackPartitionSchemeTest(SharedModuleStoreTestCase):
    """
    Tests for EnrollmentTrackPartitionScheme.
    """

    @classmethod
    def setUpClass(cls):
        super(EnrollmentTrackPartitionSchemeTest, cls).setUpClass()
        cls.course = CourseFactory.create()
        cls.student = UserFactory()

    def test_get_scheme(self):
        """
        Ensure that the scheme extension is correctly plugged in (via entry point in setup.py)
        """
        self.assertEqual(UserPartition.get_scheme('enrollment_track'), EnrollmentTrackPartitionScheme)

    def test_create_user_partition(self):
        user_partition = UserPartition.get_scheme('enrollment_track').create_user_partition(
            301, "partition", "test partition", parameters={"course_id": six.text_type(self.course.id)}
        )
        self.assertEqual(type(user_partition), EnrollmentTrackUserPartition)
        self.assertEqual(user_partition.name, "partition")

        groups = user_partition.groups
        self.assertEqual(1, len(groups))
        self.assertEqual("Audit", groups[0].name)

    def test_not_enrolled(self):
        self.assertIsNone(self._get_user_group())

    def test_default_enrollment(self):
        CourseEnrollment.enroll(self.student, self.course.id)
        self.assertEqual("Audit", self._get_user_group().name)

    def test_enrolled_in_nonexistent_mode(self):
        CourseEnrollment.enroll(self.student, self.course.id, mode=CourseMode.VERIFIED)
        self.assertEqual("Audit", self._get_user_group().name)

    def test_enrolled_in_verified(self):
        create_mode(self.course, CourseMode.VERIFIED, "Verified Enrollment Track", min_price=1)
        CourseEnrollment.enroll(self.student, self.course.id, mode=CourseMode.VERIFIED)
        self.assertEqual("Verified Enrollment Track", self._get_user_group().name)

    def test_enrolled_in_expired(self):
        create_mode(
            self.course, CourseMode.VERIFIED, "Verified Enrollment Track",
            min_price=1, expiration_datetime=datetime.now(pytz.UTC) + timedelta(days=-1)
        )
        CourseEnrollment.enroll(self.student, self.course.id, mode=CourseMode.VERIFIED)
        self.assertEqual("Verified Enrollment Track", self._get_user_group().name)

    def test_enrolled_in_non_selectable(self):
        create_mode(self.course, CourseMode.CREDIT_MODE, "Credit Enrollment Track", min_price=1)
        CourseEnrollment.enroll(self.student, self.course.id, mode=CourseMode.CREDIT_MODE)

        # The default mode is returned because Credit mode is filtered out, and no verified mode exists.
        self.assertEqual("Audit", self._get_user_group().name)

        # Now create a verified mode and check that it is returned for the learner enrolled in Credit.
        create_mode(self.course, CourseMode.VERIFIED, "Verified Enrollment Track", min_price=1)
        self.assertEqual("Verified Enrollment Track", self._get_user_group().name)

    def test_credit_after_upgrade_deadline(self):
        create_mode(self.course, CourseMode.CREDIT_MODE, "Credit Enrollment Track", min_price=1)
        CourseEnrollment.enroll(self.student, self.course.id, mode=CourseMode.CREDIT_MODE)

        # Create a verified mode and check that it is returned for the learner enrolled in Credit.
        # Make the mode "expired" to ensure that credit users can still see verified-only content after
        # the upgrade deadline has passed (see EDUCATOR-1511 for why this matters).
        create_mode(
            self.course, CourseMode.VERIFIED, "Verified Enrollment Track", min_price=1,
            expiration_datetime=datetime.now(pytz.UTC) + timedelta(days=-1)
        )
        self.assertEqual("Verified Enrollment Track", self._get_user_group().name)

    def test_using_verified_track_cohort(self):
        VerifiedTrackCohortedCourse.objects.create(course_key=self.course.id, enabled=True).save()
        CourseEnrollment.enroll(self.student, self.course.id)
        self.assertIsNone(self._get_user_group())

    def _get_user_group(self):
        """
        Gets the group the user is assigned to.
        """
        user_partition = create_enrollment_track_partition(self.course)
        return user_partition.scheme.get_group_for_user(self.course.id, self.student, user_partition)


def create_enrollment_track_partition(course):
    """
    Create an EnrollmentTrackUserPartition instance for the given course.
    """
    enrollment_track_scheme = UserPartition.get_scheme("enrollment_track")
    partition = enrollment_track_scheme.create_user_partition(
        id=1,
        name="Test Enrollment Track Partition",
        description="Test partition for segmenting users by enrollment track",
        parameters={"course_id": six.text_type(course.id)}
    )
    return partition


def create_mode(course, mode_slug, mode_name, min_price=0, expiration_datetime=None):
    """
    Create a new course mode for the given course.
    """
    return CourseMode.objects.get_or_create(
        course_id=course.id,
        mode_display_name=mode_name,
        mode_slug=mode_slug,
        min_price=min_price,
        suggested_prices='',
        _expiration_datetime=expiration_datetime,
        currency='usd'
    )
