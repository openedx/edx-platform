"""
Partition scheme for in-course reverification.

This is responsible for placing users into one of two groups,
ALLOW or DENY, for a partition associated with a particular
in-course reverification checkpoint.

NOTE: This really should be defined in the verify_student app,
which owns the verification and reverification process.
It isn't defined there now because (a) we need access to this in both Studio
and the LMS, but verify_student is specific to the LMS, and
(b) in-course reverification checkpoints currently have messaging that's
specific to credit requirements.

"""
from django.core.cache import cache

import logging

from course_modes.models import CourseMode
from lms.djangoapps.verify_student.models import SkippedReverification, VerificationStatus
from student.models import CourseEnrollment
from xmodule.partitions.partitions import NoSuchUserPartitionGroupError


log = logging.getLogger(__name__)


class VerificationPartitionScheme(object):
    """
    This scheme assigns users into the partition 'VerificationPartitionScheme'
    groups. Initially all the gated exams content will be hidden except the
    ICRV blocks for a 'verified' student until that student skips or submits
    verification for an ICRV then the related gated exam content for that ICRV
    will be displayed.

    """
    DENY = 0
    ALLOW = 1

    @classmethod
    def get_group_for_user(cls, course_key, user, user_partition):
        """
        Return the user's group depending their enrollment and verification
        status.

        Args:
            course_key(CourseKey): CourseKey
            user(User): user object
            user_partition: location object

        Returns:
            string of allowed access group
        """
        checkpoint = user_partition.parameters['location']

        # Retrieve all information we need to determine the user's group
        # as a multi-get from the cache.
        is_verified, has_skipped, has_completed = _get_user_statuses(user, course_key, checkpoint)

        # Decide whether the user should have access to content gated by this checkpoint.
        # Intuitively, we allow access if the user doesn't need to do anything at the checkpoint,
        # either because the user is in a non-verified track or the user has already submitted.
        #
        # Note that we do NOT wait the user's reverification attempt to be approved,
        # since this can take some time and the user might miss an assignment deadline.
        partition_group = (
            cls.ALLOW if not is_verified or has_skipped or has_completed
            else cls.DENY
        )

        # Return matching user partition group if it exists
        try:
            return user_partition.get_group(partition_group)
        except NoSuchUserPartitionGroupError:
            log.error(
                (
                    u"Could not find group with ID %s for verified partition "
                    "with ID %s in course %s.  The user will not be assigned a group."
                ),
                partition_group,
                user_partition.id,
                course_key
            )
            return None


def _get_user_statuses(user, course_key, checkpoint):
    """
    Retrieve all the information we need to determine the user's group.

    This will retrieve the information as a multi-get from the cache.

    Args:
        user (User): User object
        course_key (CourseKey): Identifier for the course.
        checkpoint (unicode): Location of the checkpoint in the course (serialized usage key)

    Returns:
        tuple of booleans of the form (is_verified, has_skipped, has_completed)

    """
    enrollment_cache_key = CourseEnrollment.cache_key_name(user.id, unicode(course_key))
    has_skipped_cache_key = SkippedReverification.cache_key_name(user.id, unicode(course_key))
    verification_status_cache_key = VerificationStatus.cache_key_name(user.id, unicode(course_key))

    # Try a multi-get from the cache
    cache_values = cache.get_many([
        enrollment_cache_key,
        has_skipped_cache_key,
        verification_status_cache_key
    ])

    # Retrieve whether the user is enrolled in a verified mode.
    is_verified = cache_values.get(enrollment_cache_key)
    if is_verified is None:
        is_verified = _is_enrolled_in_verified_mode(user, course_key)
        cache.set(enrollment_cache_key, is_verified)

    # Retrieve whether the user has skipped any checkpoints in this course
    has_skipped = cache_values.get(has_skipped_cache_key)
    if has_skipped is None:
        has_skipped = SkippedReverification.check_user_skipped_reverification_exists(user, course_key)
        cache.set(has_skipped_cache_key, has_skipped)

    # Retrieve the user's verification status for each checkpoint in the course.
    verification_statuses = cache_values.get(verification_status_cache_key)
    if verification_statuses is None:
        verification_statuses = VerificationStatus.get_all_checkpoints(user.id, course_key)
        cache.set(verification_status_cache_key, verification_statuses)

    # Check whether the user has completed this checkpoint
    # "Completion" here means *any* submission, regardless of its status
    # since we want to show the user the content if they've submitted
    # photos.
    checkpoint = verification_statuses.get(checkpoint)
    has_completed_check = checkpoint

    return (is_verified, has_skipped, has_completed_check)


def _is_enrolled_in_verified_mode(user, course_key):
    """
    Returns the Boolean value if given user for the given course is enrolled in
    verified modes.
    Args:
        user(User): user object
        course_key(CourseKey): CourseKey
    Returns:
        Boolean
    """
    enrollment_mode, __ = CourseEnrollment.enrollment_mode_for_user(user, course_key)
    return enrollment_mode in CourseMode.VERIFIED_MODES
