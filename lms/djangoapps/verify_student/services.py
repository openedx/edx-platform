"""
Implementation of "reverification" service to communicate with Reverification XBlock
"""

import logging

from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db import IntegrityError

from opaque_keys.edx.keys import CourseKey

from student.models import User, CourseEnrollment
from course_modes.models import CourseMode
from verify_student.models import VerificationCheckpoint, VerificationStatus, SkippedReverification


log = logging.getLogger(__name__)


class ReverificationService(object):
    """
    Reverification XBlock service
    """

    def get_status(self, user_id, course_id, related_assessment_location):
        """Get verification attempt status against a user for a given
        'checkpoint' and 'course_id'.

        Args:
            user_id(str): User Id string
            course_id(str): A string of course id
            related_assessment_location(str): Location of Reverification XBlock

        Returns:
            "skipped" if the user has skipped the re-verification or
            Verification Status string if the user has submitted photo
            verification attempt else None
        """
        course_key = CourseKey.from_string(course_id)

        # For now, treat users who aren't in the verified track the same as users
        # who clicked the "skip" button to opt out.  The messaging makes sense in
        # both cases.  Later, we may want to create a different state to prompt
        # non-verified users into the payment flow.
        if not self._is_enrolled_as_verified(user_id, course_key):
            return "skipped"
        elif SkippedReverification.check_user_skipped_reverification_exists(user_id, course_key):
            return "skipped"

        try:
            checkpoint_status = VerificationStatus.objects.filter(
                user_id=user_id,
                checkpoint__course_id=course_key,
                checkpoint__checkpoint_location=related_assessment_location
            ).latest()
            return checkpoint_status.status
        except ObjectDoesNotExist:
            return None

    def start_verification(self, course_id, related_assessment_location):
        """Create re-verification link against a verification checkpoint.

        Args:
            course_id(str): A string of course id
            related_assessment_location(str): Location of Reverification XBlock

        Returns:
            Re-verification link
        """
        course_key = CourseKey.from_string(course_id)

        # Get-or-create the verification checkpoint
        VerificationCheckpoint.get_or_create_verification_checkpoint(course_key, related_assessment_location)

        re_verification_link = reverse(
            'verify_student_incourse_reverify',
            args=(
                unicode(course_key),
                unicode(related_assessment_location)
            )
        )
        return re_verification_link

    def skip_verification(self, user_id, course_id, related_assessment_location):
        """Add skipped verification attempt entry for a user against a given
        'checkpoint'.

        Args:
            user_id(str): User Id string
            course_id(str): A string of course_id
            related_assessment_location(str): Location of Reverification XBlock

        Returns:
            None
        """
        course_key = CourseKey.from_string(course_id)
        checkpoint = VerificationCheckpoint.objects.get(
            course_id=course_key,
            checkpoint_location=related_assessment_location
        )

        # user can skip a reverification attempt only if that user has not already
        # skipped an attempt
        try:
            SkippedReverification.add_skipped_reverification_attempt(checkpoint, user_id, course_key)
        except IntegrityError:
            log.exception("Skipped attempt already exists for user %s: with course %s:", user_id, unicode(course_id))

    def get_attempts(self, user_id, course_id, related_assessment_location):
        """Get re-verification attempts against a user for a given 'checkpoint'
        and 'course_id'.

        Args:
            user_id(str): User Id string
            course_id(str): A string of course id
            related_assessment_location(str): Location of Reverification XBlock

        Returns:
            Number of re-verification attempts of a user
        """
        course_key = CourseKey.from_string(course_id)
        return VerificationStatus.get_user_attempts(user_id, course_key, related_assessment_location)

    def _is_enrolled_as_verified(self, user_id, course_key):
        """
        Check whether the user is enrolled in a verified track.

        Arguments:
            user_id (str): Identifier for the user.
            course_key (CourseKey): Identifier for the course.

        Returns: bool

        """
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            log.warning(
                (
                    "Could not find user with ID %s while checking whether "
                    "the user can submit an in-course reverification"
                ), user_id
            )
            return False

        enrollment = CourseEnrollment.get_enrollment(user, course_key)
        return (
            enrollment is not None and
            enrollment.is_active and
            enrollment.mode in CourseMode.VERIFIED_MODES
        )
