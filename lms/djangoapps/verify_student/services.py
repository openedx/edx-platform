"""
Implement the Reverification XBlock "reverification" server
"""

from opaque_keys.edx.keys import CourseKey
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from verify_student.models import VerificationCheckpoint, VerificationStatus


class ReverificationService(object):
    """ Service to implement the Reverification XBlock "reverification" service

    """

    def get_status(self, user_id, course_id, related_assessment):
        """ Check if the user has any verification attempt for this checkpoint and course_id

        Args:
            user_id(str): User Id string
            course_id(str): A string of course_id
            related_assessment(str): Verification checkpoint name

        Returns:
            Verification Status string if any attempt submitted by user else None
        """
        course_key = CourseKey.from_string(course_id)
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
