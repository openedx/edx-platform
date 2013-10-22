from auth.authz import STAFF_ROLE_NAME, INSTRUCTOR_ROLE_NAME
from auth.authz import is_user_in_course_group_role
from django.core.exceptions import PermissionDenied
from ..utils import get_course_location_for_item
from xmodule.modulestore import Location
from xmodule.modulestore.locator import CourseLocator


def get_location_and_verify_access(request, org, course, name):
    """
    Create the location, verify that the user has permissions
    to view the location. Returns the location as a Location
    """
    location = ['i4x', org, course, 'course', name]

    # check that logged in user has permissions to this item
    if not has_access(request.user, location):
        raise PermissionDenied()

    return Location(location)


def has_access(user, location, role=STAFF_ROLE_NAME):
    '''
    Return True if user allowed to access this piece of data
    Note that the CMS permissions model is with respect to courses
    There is a super-admin permissions if user.is_staff is set
    Also, since we're unifying the user database between LMS and CAS,
    I'm presuming that the course instructor (formally known as admin)
    will not be in both INSTRUCTOR and STAFF groups, so we have to cascade our
    queries here as INSTRUCTOR has all the rights that STAFF do
    '''
    if not isinstance(location, CourseLocator):
        location = get_course_location_for_item(location)
    _has_access = is_user_in_course_group_role(user, location, role)
    # if we're not in STAFF, perhaps we're in INSTRUCTOR groups
    if not _has_access and role == STAFF_ROLE_NAME:
        _has_access = is_user_in_course_group_role(
                user,
                location,
                INSTRUCTOR_ROLE_NAME
        )
    return _has_access
