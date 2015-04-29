"""
Implement the Reverification XBlock "reverification" server
"""

import logging
from opaque_keys.edx.keys import CourseKey
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from verify_student.models import VerificationCheckpoint, VerificationStatus, SkippedReverification
from django.db import IntegrityError

log = logging.getLogger(__name__)


class ReverificationService(object):
    """ Service to implement the Reverification XBlock "reverification" service

    """

    def get_status(self, user_id, course_id, related_assessment):
        """ Check if the user has any verification attempt or has skipped the verification

        Args:
            user_id(str): User Id string
            course_id(str): A string of course_id
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
        """ Get or create the verification checkpoint and return the re-verification link

        Args:
            course_id(str): A string of course_id
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
        """Create the add verification attempt

        Args:
            course_id(str): A string of course_id
            user_id(str): User Id string
            checkpoint_name(str): Verification checkpoint name

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
