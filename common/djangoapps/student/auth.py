"""
The application interface to roles which checks whether any user trying to change
authorization has authorization to do so, which infers authorization via role hierarchy
(GlobalStaff is superset of auths of course instructor, ...), which consults the config
to decide whether to check course creator role, and other such functions.
"""
from django.core.exceptions import PermissionDenied
from django.conf import settings

from student.roles import GlobalStaff, CourseCreatorRole, CourseStaffRole, CourseInstructorRole, CourseRole, \
    CourseBetaTesterRole, OrgInstructorRole, OrgStaffRole


def has_access(user, role):
    """
    Check whether this user has access to this role (either direct or implied)
    :param user:
    :param role: an AccessRole
    """
    if not user.is_active:
        return False
    # do cheapest check first even tho it's not the direct one
    if GlobalStaff().has_user(user):
        return True
    # CourseCreator is odd b/c it can be disabled via config
    if isinstance(role, CourseCreatorRole):
        # completely shut down course creation setting
        if settings.FEATURES.get('DISABLE_COURSE_CREATION', False):
            return False
        # wide open course creation setting
        if not settings.FEATURES.get('ENABLE_CREATOR_GROUP', False):
            return True

    if role.has_user(user):
        return True
    # if not, then check inferred permissions
    if (isinstance(role, (CourseStaffRole, CourseBetaTesterRole)) and
            CourseInstructorRole(role.course_key).has_user(user)):
        return True
    return False


def has_course_access(user, course_key, role=CourseStaffRole):
    """
    Return True if user allowed to access this course_id
    Note that the CMS permissions model is with respect to courses
    There is a super-admin permissions if user.is_staff is set
    Also, since we're unifying the user database between LMS and CAS,
    I'm presuming that the course instructor (formally known as admin)
    will not be in both INSTRUCTOR and STAFF groups, so we have to cascade our
    queries here as INSTRUCTOR has all the rights that STAFF do.

    :param user:
    :param course_key: A course key
    :param role: an AccessRole
    """
    if GlobalStaff().has_user(user):
        return True
    if OrgInstructorRole(org=course_key.org).has_user(user):
        return True
    if OrgStaffRole(org=course_key.org).has_user(user):
        return True
    # temporary to ensure we give universal access given a course until we impl branch specific perms
    return has_access(user, role(course_key.for_branch(None)))


def add_users(caller, role, *users):
    """
    The caller requests adding the given users to the role. Checks that the caller
    has sufficient authority.

    :param caller: a user
    :param role: an AccessRole
    """
    _check_caller_authority(caller, role)
    role.add_users(*users)


def remove_users(caller, role, *users):
    """
    The caller requests removing the given users from the role. Checks that the caller
    has sufficient authority.

    :param caller: a user
    :param role: an AccessRole
    """
    # can always remove self (at this layer)
    if not(len(users) == 1 and caller == users[0]):
        _check_caller_authority(caller, role)
    role.remove_users(*users)


def _check_caller_authority(caller, role):
    """
    Internal function to check whether the caller has authority to manipulate this role
    :param caller: a user
    :param role: an AccessRole
    """
    if not (caller.is_authenticated() and caller.is_active):
        raise PermissionDenied
    # superuser
    if GlobalStaff().has_user(caller):
        return

    if isinstance(role, (GlobalStaff, CourseCreatorRole)):
        raise PermissionDenied
    elif isinstance(role, CourseRole):  # instructors can change the roles w/in their course
        if not has_access(caller, CourseInstructorRole(role.course_key)):
            raise PermissionDenied
