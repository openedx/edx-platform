""" Helper methods for determining user access permissions in Studio """

from student.roles import CourseInstructorRole
from student import auth


def get_user_role(user, course_id):
    """
    What type of access: staff or instructor does this user have in Studio?

    No code should use this for access control, only to quickly serialize the type of access
    where this code knows that Instructor trumps Staff and assumes the user has one or the other.

    This will not return student role because its purpose for using in Studio.

    :param course_id: the course_id of the course we're interested in
    """
    # afaik, this is only used in lti
    if auth.user_has_role(user, CourseInstructorRole(course_id)):
        return 'instructor'
    else:
        return 'staff'
