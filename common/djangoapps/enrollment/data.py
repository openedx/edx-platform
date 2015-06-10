"""
Data Aggregation Layer of the Enrollment API. Collects all enrollment specific data into a single
source to be used throughout the API.

"""
import logging
from django.contrib.auth.models import User
from opaque_keys.edx.keys import CourseKey
from xmodule.modulestore.django import modulestore
from enrollment.errors import (
    CourseNotFoundError, CourseEnrollmentClosedError, CourseEnrollmentFullError,
    CourseEnrollmentExistsError, UserNotFoundError,
)
from enrollment.serializers import CourseEnrollmentSerializer, CourseField
from student.models import (
    CourseEnrollment, NonExistentCourseError, EnrollmentClosedError,
    CourseFullError, AlreadyEnrolledError,
)

log = logging.getLogger(__name__)


def get_course_enrollments(user_id):
    """Retrieve a list representing all aggregated data for a user's course enrollments.

    Construct a representation of all course enrollment data for a specific user.

    Args:
        user_id (str): The name of the user to retrieve course enrollment information for.

    Returns:
        A serializable list of dictionaries of all aggregated enrollment data for a user.

    """
    qset = CourseEnrollment.objects.filter(
        user__username=user_id, is_active=True
    ).order_by('created')
    return CourseEnrollmentSerializer(qset).data  # pylint: disable=no-member


def get_course_enrollment(username, course_id):
    """Retrieve an object representing all aggregated data for a user's course enrollment.

    Get the course enrollment information for a specific user and course.

    Args:
        username (str): The name of the user to retrieve course enrollment information for.
        course_id (str): The course to retrieve course enrollment information for.

    Returns:
        A serializable dictionary representing the course enrollment.

    """
    course_key = CourseKey.from_string(course_id)
    try:
        enrollment = CourseEnrollment.objects.get(
            user__username=username, course_id=course_key
        )
        return CourseEnrollmentSerializer(enrollment).data  # pylint: disable=no-member
    except CourseEnrollment.DoesNotExist:
        return None


def create_course_enrollment(username, course_id, mode, is_active):
    """Create a new course enrollment for the given user.

    Creates a new course enrollment for the specified user username.

    Args:
        username (str): The name of the user to create a new course enrollment for.
        course_id (str): The course to create the course enrollment for.
        mode (str): (Optional) The mode for the new enrollment.
        is_active (boolean): (Optional) Determines if the enrollment is active.

    Returns:
        A serializable dictionary representing the new course enrollment.

    Raises:
        CourseNotFoundError
        CourseEnrollmentFullError
        EnrollmentClosedError
        CourseEnrollmentExistsError

    """
    course_key = CourseKey.from_string(course_id)

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        msg = u"Not user with username '{username}' found.".format(username=username)
        log.warn(msg)
        raise UserNotFoundError(msg)

    try:
        enrollment = CourseEnrollment.enroll(user, course_key, check_access=True)
        return _update_enrollment(enrollment, is_active=is_active, mode=mode)
    except NonExistentCourseError as err:
        raise CourseNotFoundError(err.message)
    except EnrollmentClosedError as err:
        raise CourseEnrollmentClosedError(err.message)
    except CourseFullError as err:
        raise CourseEnrollmentFullError(err.message)
    except AlreadyEnrolledError as err:
        enrollment = get_course_enrollment(username, course_id)
        raise CourseEnrollmentExistsError(err.message, enrollment)


def update_course_enrollment(username, course_id, mode=None, is_active=None):
    """Modify a course enrollment for a user.

    Allows updates to a specific course enrollment.

    Args:
        username (str): The name of the user to retrieve course enrollment information for.
        course_id (str): The course to retrieve course enrollment information for.
        mode (str): (Optional) If specified, modify the mode for this enrollment.
        is_active (boolean): (Optional) Determines if the enrollment is active.

    Returns:
        A serializable dictionary representing the modified course enrollment.

    """
    course_key = CourseKey.from_string(course_id)

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        msg = u"Not user with username '{username}' found.".format(username=username)
        log.warn(msg)
        raise UserNotFoundError(msg)

    try:
        enrollment = CourseEnrollment.objects.get(user=user, course_id=course_key)
        return _update_enrollment(enrollment, is_active=is_active, mode=mode)
    except CourseEnrollment.DoesNotExist:
        return None


def _update_enrollment(enrollment, is_active=None, mode=None):
    enrollment.update_enrollment(is_active=is_active, mode=mode)
    enrollment.save()
    return CourseEnrollmentSerializer(enrollment).data  # pylint: disable=no-member


def get_course_enrollment_info(course_id, include_expired=False):
    """Returns all course enrollment information for the given course.

    Based on the course id, return all related course information..

    Args:
        course_id (str): The course to retrieve enrollment information for.

        include_expired (bool): Boolean denoting whether expired course modes
        should be included in the returned JSON data.

    Returns:
        A serializable dictionary representing the course's enrollment information.

    Raises:
        CourseNotFoundError

    """
    course_key = CourseKey.from_string(course_id)
    course = modulestore().get_course(course_key)
    if course is None:
        msg = u"Requested enrollment information for unknown course {course}".format(course=course_id)
        log.warning(msg)
        raise CourseNotFoundError(msg)
    return CourseField().to_native(course, include_expired=include_expired)
