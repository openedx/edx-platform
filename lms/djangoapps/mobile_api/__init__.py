from xmodule.modulestore.django import modulestore
from rest_framework.exceptions import PermissionDenied
from courseware.access import has_access


def get_mobile_course(course_id, user=None):
    """
    Return only courses that have mobile_available set to True
    """
    course = modulestore().get_course(course_id, depth=None)

    if not course.mobile_available or not has_access(user, 'staff', course):
        raise PermissionDenied(detail="Course not available on mobile.")
    return course


def mobile_course_enrollments(enrollments, user):
    """
    Return enrollments only if courses are mobile_available (or if the user has staff access)
    enrollments is a list of CourseEnrollments.
    """
    for enr in enrollments:
        course = enr.course
        if course.mobile_available:
            yield enr
        elif has_access(user, 'staff', course):
            yield enr
