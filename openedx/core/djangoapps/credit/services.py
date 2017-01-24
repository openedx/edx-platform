"""
Implementation of "credit" XBlock service
"""

import logging

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

from opaque_keys.edx.keys import CourseKey

from student.models import CourseEnrollment
from xmodule.modulestore.django import modulestore

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

    def is_credit_course(self, course_key_or_id):
        """
        Returns boolean if the passed in course_id (string) or course_key is
        a credit_course
        """

        # This seems to need to be here otherwise we get
        # circular references when starting up the app
        from openedx.core.djangoapps.credit.api.eligibility import (
            is_credit_course,
        )

        course_key = _get_course_key(course_key_or_id)

        return is_credit_course(course_key)

    def get_credit_state(self, user_id, course_key_or_id, return_course_info=False):
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
                'is_credit_course': if the course has been marked as a credit bearing course
                'credit_requirement_status': the user's status in fulfilling those requirements
                'course_name': optional display name of the course
                'course_end_date': optional end date of the course
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

        result = {
            'enrollment_mode': enrollment.mode,
            'profile_fullname': user.profile.name,
            'student_email': user.email,
            'is_credit_course': is_credit_course(course_key),
            'credit_requirement_status': get_credit_requirement_status(course_key, user.username)
        }

        if return_course_info:
            course = modulestore().get_course(course_key, depth=0)
            result.update({
                'course_name': course.display_name,
                'course_end_date': course.end,
            })
        return result

    def set_credit_requirement_status(self, user_id, course_key_or_id, req_namespace,
                                      req_name, status="satisfied", reason=None):
        """
        A simple wrapper around the method of the same name in api.eligibility.py. The only difference is
        that a user_id is passed in.

        For more information, see documentation on this method name in api.eligibility.py
        """

        # This seems to need to be here otherwise we get
        # circular references when starting up the app
        from openedx.core.djangoapps.credit.api.eligibility import (
            is_credit_course,
            set_credit_requirement_status as api_set_credit_requirement_status
        )

        course_key = _get_course_key(course_key_or_id)

        # quick exit, if course is not credit enabled
        if not is_credit_course(course_key):
            return

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

        api_set_credit_requirement_status(
            user,
            course_key,
            req_namespace,
            req_name,
            status,
            reason
        )

    def remove_credit_requirement_status(self, user_id, course_key_or_id, req_namespace, req_name):
        """
        A simple wrapper around the method of the same name in
        api.eligibility.py. The only difference is that a user_id
        is passed in.

        For more information, see documentation on this method name
        in api.eligibility.py
        """

        # This seems to need to be here otherwise we get
        # circular references when starting up the app
        from openedx.core.djangoapps.credit.api.eligibility import (
            is_credit_course,
            remove_credit_requirement_status as api_remove_credit_requirement_status
        )

        course_key = _get_course_key(course_key_or_id)

        # quick exit, if course is not credit enabled
        if not is_credit_course(course_key):
            return

        # always log any deleted activity to the credit requirements
        # table. This will be to help debug any issues that might
        # arise in production
        log_msg = (
            'remove_credit_requirement_status was called with '
            'user_id={user_id}, course_key_or_id={course_key_or_id} '
            'req_namespace={req_namespace}, req_name={req_name}, '.format(
                user_id=user_id,
                course_key_or_id=course_key_or_id,
                req_namespace=req_namespace,
                req_name=req_name
            )
        )
        log.info(log_msg)

        # need to get user_name from the user object
        try:
            user = User.objects.get(id=user_id)
        except ObjectDoesNotExist:
            return None

        api_remove_credit_requirement_status(
            user.username,
            course_key,
            req_namespace,
            req_name
        )
