"""
Provides partition support to the user service.
"""
from django.core.cache import cache

import logging

from course_modes.models import CourseMode
from lms.djangoapps.verify_student.models import SkippedReverification, VerificationStatus
from student.models import CourseEnrollment


log = logging.getLogger(__name__)


class VerificationPartitionScheme(object):
    """
    This scheme assigns users into the partition 'VerificationPartitionScheme'
    groups. Initially all the gated exams content will be hidden except the
    ICRV blocks for a 'verified' student until that student skips or submits
    verification for an ICRV then the related gated exam content for that ICRV
    will be displayed.

    Following scenarios can be handled:

    non_verified: When a student is not enrolled as 'verified'
    all ICRV blocks will be hidden but the student will have access
    to all the gated exams content.

    verified_allow: When a student skips or submits or denied at any
    ICRV checkpoint verification then that student will be allowed to access
    the gated exam content of that ICRV.

    verified_deny: When a student has failed (used all attempts) an ICRV verification,
    all ICRV blocks will be hidden and the student will have access to all
    the gated exams content.
    """
    NON_VERIFIED = 'non_verified'
    VERIFIED_ALLOW = 'verified_allow'
    VERIFIED_DENY = 'verified_deny'

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
        # here getting cache key names for all models. So that we can make the
        # list of keys and get the cache.get_many

        enrollment_cache_key = CourseEnrollment.cache_key_name(user.id, unicode(course_key))
        has_skipped_cache_key = SkippedReverification.cache_key_name(user.id, unicode(course_key))
        verification_status_cache_key = VerificationStatus.cache_key_name(user.id, unicode(course_key))

        cache_keys = [
            enrollment_cache_key, has_skipped_cache_key, verification_status_cache_key
        ]

        cache_values = cache.get_many(cache_keys)

        if enrollment_cache_key not in cache_values:
            is_verified = is_enrolled_in_verified_mode(user, course_key)
        else:
            enrollment_mode = cache_values[enrollment_cache_key]
            is_verified = enrollment_mode in CourseMode.VERIFIED_MODES

        if has_skipped_cache_key not in cache_values:
            has_skipped = has_skipped_any_checkpoint(user, course_key)
        else:
            has_skipped = cache_values[has_skipped_cache_key]

        if verification_status_cache_key not in cache_values:
            verification_statuses = VerificationStatus.get_all_checkpoints(user.id, course_key)
        else:
            verification_statuses = cache_values[verification_status_cache_key]

        was_denied = VerificationStatus.DENIED_STATUS in verification_statuses.values()
        has_completed_check = checkpoint in verification_statuses and (
            verification_statuses[checkpoint] in [
                VerificationStatus.SUBMITTED_STATUS, VerificationStatus.APPROVED_STATUS
            ]
        )

        if not is_verified:
            # the course content tagged with given 'user_partition' is
            # accessible/visible to all the students
            return cls.NON_VERIFIED
        elif has_skipped or was_denied or has_completed_check:
            # the course content tagged with given 'user_partition' is
            # accessible/visible to the students enrolled as `verified` users
            # and has either `skipped any ICRV` or `was denied at any ICRV
            # (used all attempts for an ICRV but still denied by the software
            # secure)` or `has submitted/approved verification for given ICRV`
            return cls.VERIFIED_ALLOW
        else:
            # the course content tagged with given 'user_partition' is
            # accessible/visible to the students enrolled as `verified` users
            # and has not yet submitted for the related ICRV
            return cls.VERIFIED_DENY

    @classmethod
    def key_for_partition(cls, xblock_location_id):
        """ Returns the key for partition scheme to use for look up and save
        the user's group for a given 'VerificationPartitionScheme'.

        Args:
            xblock_location_id(str): Location of block in course

        Returns:
            String of the format 'verification:{location}'
        """
        return 'verification:{0}'.format(xblock_location_id)


def is_enrolled_in_verified_mode(user, course_key):
    """
    Returns the Boolean value if given user for the given course is enrolled in
    verified modes.

    Args:
        user(User): user object
        course_key(CourseKey): CourseKey

    Returns:
        Boolean
    """
    # Don't get from cache because this is get through get_many() call from caller
    cache_key = CourseEnrollment.cache_key_name(user.id, unicode(course_key))
    enrollment_mode, __ = CourseEnrollment.enrollment_mode_for_user(user, course_key)
    # Set the cache so that get_many call get it.
    cache.set(cache_key, enrollment_mode)

    return enrollment_mode in CourseMode.VERIFIED_MODES


def was_denied_at_any_checkpoint(user, course_key):
    """Returns the Boolean value if given user with given course was denied for any
    incourse verification checkpoint.

    Args:
        user(User): user object
        course_key(CourseKey): CourseKey

    Returns:
        Boolean
    """
    checkpoints_dict = VerificationStatus.get_all_checkpoints(user.id, course_key)
    return VerificationStatus.DENIED_STATUS in checkpoints_dict.values()


def has_skipped_any_checkpoint(user, course_key):
    """Check existence of a user's skipped re-verification attempt for a
    specific course.

    Args:
        user(User): user object
        course_key(CourseKey): CourseKey

    Returns:
        Boolean
    """
    return SkippedReverification.check_user_skipped_reverification_exists(user, course_key)


def has_completed_checkpoint(user, course_key, checkpoint):
    """
    Get re-verification status against a user for a 'course_id' and checkpoint.
    Only 'approved' and 'submitted' statuses are considered as completed.

    Args:
        user (User): The user whose status we are retrieving.
        course_key (CourseKey): The identifier for the course.
        checkpoint (UsageKey): The location of the checkpoint in the course.

    Returns:
        Boolean
    """

    checkpoints_dict = VerificationStatus.get_all_checkpoints(user.id, course_key)
    return checkpoint in checkpoints_dict and checkpoints_dict[checkpoint] in [
        VerificationStatus.SUBMITTED_STATUS, VerificationStatus.APPROVED_STATUS
    ]
