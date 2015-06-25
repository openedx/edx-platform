"""
Implementation of "reverification" service to communicate with Reverification XBlock
"""

import logging

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db import IntegrityError

from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.credit.exceptions import InvalidCreditRequirements
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
            return

        from openedx.core.djangoapps.credit.api import get_credit_requirement, set_credit_requirement_status
        namespace = "reverification"
        credit_requirement = get_credit_requirement(
            course_key, namespace, checkpoint.checkpoint_location
        )
        if credit_requirement is None:
            log.error(
                u"Failed to find credit requirement with course_key '%s', namespace '%s', location '%s'.",
                course_key,
                namespace,
                checkpoint.checkpoint_location
            )
            return

        try:
            set_credit_requirement_status(
                User.objects.get(id=user_id).username,
                course_key,
                credit_requirement['namespace'],
                credit_requirement['name'],
                "skipped"
            )
        except InvalidCreditRequirements:
            # log exception if unable to add credit requirement status for user
            log.error(
                u"Failed to add credit requirement status for user with id '%d'.",
                user_id,
                exc_info=True
            )

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

    def display_unfulfilled_credit_requirement(self, user_id, course_id, usage_key):
        """Check if provided 'usage_key' is related to a credit requirement
        and its status is 'failed' or 'skipped', for a user against a course.

        Find the credit requirements which user has skipped or failed.

        Args:
            user_id(str): User Id string
            course_id(str): A string of course id

        Returns:
            Boolean if the module related to provided 'usage_key' should
            display in courseware.

        """
        from openedx.core.djangoapps.credit.api import get_credit_requirement_status
        credit_requirements_status = get_credit_requirement_status(
            course_id, User.objects.get(id=user_id).username
        )
        is_skipped = False
        is_credit_requirement = False
        requirement_status = None
        for requirement in credit_requirements_status:
            # if provided usage key of a module is not present in credit
            # requirements list than show that module as default
            if requirement['status'] == 'skipped':
                is_skipped = True
            if requirement['name'] == unicode(usage_key):
                is_credit_requirement = True
                requirement_status = requirement['status']

        if is_credit_requirement and is_skipped:
            # user has skipped a credit requirement so don't display any
            # credit requirement block in student view
            return False
        if is_credit_requirement and not is_skipped and requirement_status == 'failed':
            # user has failed a credit requirement so hide all credit
            # requirement blocks except with failed status
            return False

        return True
