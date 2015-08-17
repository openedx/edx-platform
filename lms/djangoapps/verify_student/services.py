"""
Implementation of "reverification" service to communicate with Reverification XBlock
"""

import logging

from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db import IntegrityError

from opaque_keys.edx.keys import CourseKey

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
        has_skipped = SkippedReverification.check_user_skipped_reverification_exists(user_id, course_key)
        if has_skipped:
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
        VerificationCheckpoint.objects.get_or_create(
            course_id=course_key,
            checkpoint_location=related_assessment_location
        )

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
