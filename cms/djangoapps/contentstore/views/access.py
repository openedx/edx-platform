""" Helper methods for determining user access permissions in Studio """


from common.djangoapps.student import auth
from common.djangoapps.student.roles import CourseInstructorRole
from openedx.core.djangoapps.course_roles.helpers import course_permission_check
from openedx.core.djangoapps.course_roles.permissions import CourseRolesPermission


def get_user_role(user, course_id):
    """
    What type of access: staff or instructor does this user have in Studio?

    No code should use this for access control, only to quickly serialize the type of access
    where this code knows that Instructor trumps Staff and assumes the user has one or the other.

    This will not return student role because its purpose for using in Studio.

    :param course_id: the course_id of the course we're interested in
    """
    # afaik, this is only used in lti

    # TODO: course roles: If the course roles feature flag is disabled the course_permission_check
    # call below will never return true.
    # Remove the auth.has_user_role call when course_roles Django app are implemented.
    if (
        auth.user_has_role(user, CourseInstructorRole(course_id)) or
        course_permission_check(user, CourseRolesPermission.MANAGE_ALL_USERS.value, course_id)
    ):
        return 'instructor'
    else:
        return 'staff'
