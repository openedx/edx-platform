"""
Encapsulates permissions checks for Course Blocks API
"""
from django.contrib.auth.models import User
from opaque_keys.edx.keys import CourseKey

from lms.djangoapps.courseware.access import has_access
from lms.djangoapps.courseware.access_response import AccessResponse
from lms.djangoapps.courseware.access_utils import ACCESS_DENIED, ACCESS_GRANTED, check_public_access
from lms.djangoapps.courseware.courses import get_course
from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.student.roles import CourseStaffRole
from xmodule.course_module import COURSE_VISIBILITY_PUBLIC


def can_access_all_blocks(requesting_user, course_key):
    """
    Returns whether the requesting_user can access all the blocks
    in the course.
    """
    return has_access(requesting_user, CourseStaffRole.ROLE, course_key)


def can_access_others_blocks(requesting_user, course_key):
    """
    Returns whether the requesting_user can access the blocks for
    other users in the given course.
    """
    return has_access(requesting_user, CourseStaffRole.ROLE, course_key)


def can_access_self_blocks(requesting_user: User, course_key: CourseKey) -> AccessResponse:
    """
    Returns whether the requesting_user can access own blocks.
    """
    user_is_enrolled_or_staff = (  # pylint: disable=consider-using-ternary
        (requesting_user.id and CourseEnrollment.is_enrolled(requesting_user, course_key)) or
        has_access(requesting_user, CourseStaffRole.ROLE, course_key)
    )
    if user_is_enrolled_or_staff:
        return ACCESS_GRANTED
    try:
        return is_course_public(course_key)
    except ValueError:
        return ACCESS_DENIED


def is_course_public(course_key: CourseKey) -> AccessResponse:
    """
    This checks if a course is publicly accessible or not.
    """
    course = get_course(course_key, depth=0)
    return check_public_access(course, [COURSE_VISIBILITY_PUBLIC])
