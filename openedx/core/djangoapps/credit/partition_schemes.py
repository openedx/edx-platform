"""
Provides partition support to the user service.
"""

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
    NON_VERIFIED = 0
    VERIFIED_ALLOW = 1
    VERIFIED_DENY = 2

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

        if (
                not is_enrolled_in_verified_mode(user, course_key)
        ):
            # the course content tagged with given 'user_partition' is
            # accessible/visible to all the students
            return cls.NON_VERIFIED
        elif (
                has_skipped_any_checkpoint(user, course_key) or
                was_denied_at_any_checkpoint(user, course_key) or
                has_completed_checkpoint(user, course_key, checkpoint)
        ):
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
    enrollment_mode, __ = CourseEnrollment.enrollment_mode_for_user(user, course_key)
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
    return VerificationStatus.objects.filter(
        user=user,
        checkpoint__course_id=course_key,
        status='denied'
    ).exists()


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
        unicode or None
    """
    return VerificationStatus.check_user_has_completed_checkpoint(user, course_key, checkpoint)
