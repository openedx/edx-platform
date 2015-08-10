"""
Implementation of "credit" XBlock service
"""

import logging

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

from opaque_keys.edx.keys import CourseKey

from student.models import CourseEnrollment

log = logging.getLogger(__name__)


def _get_course_key(course_key_or_id):
    """
    Helper method to get a course key eith from a string or a CourseKey,
    where the CourseKey will simply be returned
    """
    return (
        CourseKey.from_string(course_key_or_id)
        if isinstance(course_key_or_id, basestring)
        else course_key_or_id
    )


class CreditService(object):
    """
    Course Credit XBlock service
    """

    def get_credit_state(self, user_id, course_key_or_id):
        """
        Return all information about the user's credit state inside of a given
        course.

        ARGS:
            - user_id: The PK of the User in question
            - course_key: The course ID (as string or CourseKey)

        RETURNS:
            NONE (user not found or is not enrolled or is not credit course)
            - or -
            {
                'enrollment_mode': the mode that the user is enrolled in the course
                'profile_fullname': the name that the student registered under, used for verification
                'credit_requirement_status': the user's status in fulfilling those requirements
            }
        """

        # This seems to need to be here otherwise we get
        # circular references when starting up the app
        from openedx.core.djangoapps.credit.api.eligibility import (
            is_credit_course,
            get_credit_requirement_status,
        )

        # since we have to do name matching during various
        # verifications, User must have a UserProfile
        try:
            user = User.objects.select_related('profile').get(id=user_id)
        except ObjectDoesNotExist:
            # bad user_id
            return None

        course_key = _get_course_key(course_key_or_id)

        enrollment = CourseEnrollment.get_enrollment(user, course_key)
        if not enrollment or not enrollment.is_active:
            # not enrolled
            return None

        if not is_credit_course(course_key):
            return None

        return {
            'enrollment_mode': enrollment.mode,
            'profile_fullname': user.profile.name,
            'credit_requirement_status': get_credit_requirement_status(course_key, user.username)
        }

    def set_credit_requirement_status(self, user_id, course_key_or_id, req_namespace,
                                      req_name, status="satisfied", reason=None):
        """
        A simple wrapper around the method of the same name in api.eligibility.py. The only difference is
        that a user_id is passed in.

        For more information, see documentation on this method name in api.eligibility.py
        """

        # always log any update activity to the credit requirements
        # table. This will be to help debug any issues that might
        # arise in production
        log_msg = (
            'set_credit_requirement_status was called with '
            'user_id={user_id}, course_key_or_id={course_key_or_id} '
            'req_namespace={req_namespace}, req_name={req_name}, '
            'status={status}, reason={reason}'.format(
                user_id=user_id,
                course_key_or_id=course_key_or_id,
                req_namespace=req_namespace,
                req_name=req_name,
                status=status,
                reason=reason
            )
        )
        log.info(log_msg)

        # need to get user_name from the user object
        try:
            user = User.objects.get(id=user_id)
        except ObjectDoesNotExist:
            return None

        course_key = _get_course_key(course_key_or_id)

        # This seems to need to be here otherwise we get
        # circular references when starting up the app
        from openedx.core.djangoapps.credit.api.eligibility import (
            set_credit_requirement_status as api_set_credit_requirement_status
        )

        api_set_credit_requirement_status(
            user.username,
            course_key,
            req_namespace,
            req_name,
            status,
            reason
        )
