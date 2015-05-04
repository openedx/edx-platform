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

    def get_status(self, user_id, course_id, related_assessment):
        """
        Get verification attempt status against a user for a given 'checkpoint'
        and 'course_id'.

        Args:
            user_id(str): User Id string
            course_id(str): A string of course id
            related_assessment(str): Verification checkpoint name

        Returns:
            "skipped" if has skip the re-verification or Verification Status string if
            any attempt submitted by user else None
        """
        course_key = CourseKey.from_string(course_id)
        has_skipped = SkippedReverification.check_user_skipped_reverification_exists(user_id, course_key)
        if has_skipped:
            return "skipped"
        try:
            checkpoint_status = VerificationStatus.objects.filter(
                user_id=user_id,
                checkpoint__course_id=course_key,
                checkpoint__checkpoint_name=related_assessment
            ).latest()
            return checkpoint_status.status
        except ObjectDoesNotExist:
            return None

    def start_verification(self, course_id, related_assessment, item_id):
        """
        Create re-verification link against a verification checkpoint.

        Args:
            course_id(str): A string of course id
            related_assessment(str): Verification checkpoint name

        Returns:
            Re-verification link
        """
        course_key = CourseKey.from_string(course_id)
        VerificationCheckpoint.objects.get_or_create(course_id=course_key, checkpoint_name=related_assessment)
        re_verification_link = reverse(
            'verify_student_incourse_reverify',
            args=(
                unicode(course_key),
                unicode(related_assessment),
                unicode(item_id)
            )
        )
        return re_verification_link

    def skip_verification(self, checkpoint_name, user_id, course_id):
        """
        Add skipped verification attempt entry against a given 'checkpoint'

        Args:
            checkpoint_name(str): Verification checkpoint name
            user_id(str): User Id string
            course_id(str): A string of course_id

        Returns:
            None
        """
        course_key = CourseKey.from_string(course_id)
        checkpoint = VerificationCheckpoint.objects.get(course_id=course_key, checkpoint_name=checkpoint_name)

        # if user do not already skipped the attempt for this course only then he can skip
        try:
            SkippedReverification.add_skipped_reverification_attempt(checkpoint, user_id, course_key)
        except IntegrityError:
            log.exception("Skipped attempt already exists for user %s: with course %s:", user_id, unicode(course_id))

    def get_attempts(self, user_id, course_id, related_assessment, location_id):
        """
        Get re-verification attempts against a user for a given 'checkpoint'
        and 'course_id'.

        Args:
            user_id(str): User Id string
            course_id(str): A string of course id
            related_assessment(str): Verification checkpoint name
            location_id(str): Location of Reverification XBlock in courseware

        Returns:
            Number of re-verification attempts of a user
        """
        course_key = CourseKey.from_string(course_id)
        return VerificationStatus.get_user_attempts(user_id, course_key, related_assessment, location_id)
