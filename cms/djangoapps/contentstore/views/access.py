""" Helper methods for determining user access permissions in Studio """


from common.djangoapps.student import auth
from common.djangoapps.student.roles import CourseInstructorRole
from openedx.core.djangoapps.course_roles.data import CourseRolesPermission


def get_user_role(user, course_id):
    """
    What type of access: staff or instructor does this user have in Studio?

    No code should use this for access control, only to quickly serialize the type of access
    where this code knows that Instructor trumps Staff and assumes the user has one or the other.

    This will not return student role because its purpose for using in Studio.

    :param course_id: the course_id of the course we're interested in
    """
    # afaik, this is only used in lti
    # TODO: remove role checks once course_roles is fully implemented and data is migrated
    if (
        auth.user_has_role(user, CourseInstructorRole(course_id)) or
        user.has_perm(CourseRolesPermission.MANAGE_ALL_USERS.perm_name, course_id)
    ):
        return 'instructor'
    else:
        return 'staff'
