"""
Implementation of "credit" XBlock service
"""

import logging

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

#from opaque_keys.edx.keys import CourseKey

from student.models import CourseEnrollment

log = logging.getLogger(__name__)


class CreditService(object):
    """
    Course Credit XBlock service
    """

    def get_credit_state(self, user_id, course_key):
        """
        Return all information about the user's credit state inside of a given
        course.

        ARGS:
            - user_id: The PK of the User in question
            - course_key: The course ID (as string)

        RETURNS:
            NONE (user not found or is not enrolled or is not credit course)
            - or -
            {
                'enrollment_mode': the mode that the user is enrolled in the course
                'credit_requirements': the requirements (dict) in order to eligible for credit
                'credit_requirement_status': the user's status in fulfilling those requirements
            }
        """

        # This seems to need to be here otherwise we get
        # circular references when starting up the app
        from openedx.core.djangoapps.credit.api.eligibility import (
            is_credit_course,
            get_credit_requirements,
            get_credit_requirement_status,
        )

        # course_key = CourseKey.from_string(course_id)

        try:
            user = User.objects.get(id=user_id)
        except ObjectDoesNotExist:
            # bad user_id
            return None

        enrollment = CourseEnrollment.get_enrollment(user, course_key)
        if not enrollment or not enrollment.is_active:
            # not enrolled
            return None

        if not is_credit_course(course_key):
            return None

        return {
            'enrollment_mode': enrollment.mode,
            'credit_requirements': get_credit_requirements(course_key),
            'credit_requirement_status': get_credit_requirement_status(course_key, user.username)
        }
