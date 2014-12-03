"""
Data Aggregation Layer of the Enrollment API. Collects all enrollment specific data into a single
source to be used throughout the API.

"""
import logging
from django.contrib.auth.models import User
from opaque_keys.edx.keys import CourseKey
from xmodule.modulestore.django import modulestore
from enrollment.serializers import CourseEnrollmentSerializer, CourseField
from student.models import CourseEnrollment, NonExistentCourseError

log = logging.getLogger(__name__)


def get_course_enrollments(student_id):
    """Retrieve a list representing all aggregated data for a student's course enrollments.

    Construct a representation of all course enrollment data for a specific student.

    Args:
        student_id (str): The name of the student to retrieve course enrollment information for.

    Returns:
        A serializable list of dictionaries of all aggregated enrollment data for a student.

    """
    qset = CourseEnrollment.objects.filter(
        user__username=student_id, is_active=True
    ).order_by('created')
    return CourseEnrollmentSerializer(qset).data  # pylint: disable=no-member


def get_course_enrollment(student_id, course_id):
    """Retrieve an object representing all aggregated data for a student's course enrollment.

    Get the course enrollment information for a specific student and course.

    Args:
        student_id (str): The name of the student to retrieve course enrollment information for.
        course_id (str): The course to retrieve course enrollment information for.

    Returns:
        A serializable dictionary representing the course enrollment.

    """
    course_key = CourseKey.from_string(course_id)
    try:
        enrollment = CourseEnrollment.objects.get(
            user__username=student_id, course_id=course_key
        )
        return CourseEnrollmentSerializer(enrollment).data  # pylint: disable=no-member
    except CourseEnrollment.DoesNotExist:
        return None


def update_course_enrollment(student_id, course_id, mode=None, is_active=None):
    """Modify a course enrollment for a student.

    Allows updates to a specific course enrollment.

    Args:
        student_id (str): The name of the student to retrieve course enrollment information for.
        course_id (str): The course to retrieve course enrollment information for.
        mode (str): (Optional) The mode for the new enrollment.
        is_active (boolean): (Optional) Determines if the enrollment is active.

    Returns:
        A serializable dictionary representing the modified course enrollment.

    """
    course_key = CourseKey.from_string(course_id)
    student = User.objects.get(username=student_id)
    if not CourseEnrollment.is_enrolled(student, course_key):
        enrollment = CourseEnrollment.enroll(student, course_key, check_access=True)
    else:
        enrollment = CourseEnrollment.objects.get(user=student, course_id=course_key)

    enrollment.update_enrollment(is_active=is_active, mode=mode)
    enrollment.save()
    return CourseEnrollmentSerializer(enrollment).data  # pylint: disable=no-member


def get_course_enrollment_info(course_id):
    """Returns all course enrollment information for the given course.

    Based on the course id, return all related course information..

    Args:
        course_id (str): The course to retrieve enrollment information for.

    Returns:
        A serializable dictionary representing the course's enrollment information.

    """
    course_key = CourseKey.from_string(course_id)
    course = modulestore().get_course(course_key)
    if course is None:
        log.warning(
            u"Requested enrollment information for unknown course {course}"
            .format(course=course_id)
        )
        raise NonExistentCourseError
    return CourseField().to_native(course)
