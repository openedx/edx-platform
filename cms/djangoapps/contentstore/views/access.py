from student.roles import CourseStaffRole, GlobalStaff, CourseInstructorRole
from student import auth


def has_course_access(user, course_id, role=CourseStaffRole):
    """
    Return True if user allowed to access this course_id
    Note that the CMS permissions model is with respect to courses
    There is a super-admin permissions if user.is_staff is set
    Also, since we're unifying the user database between LMS and CAS,
    I'm presuming that the course instructor (formally known as admin)
    will not be in both INSTRUCTOR and STAFF groups, so we have to cascade our
    queries here as INSTRUCTOR has all the rights that STAFF do
    """
    if GlobalStaff().has_user(user):
        return True
    return auth.has_access(user, role(course_id))


def get_user_role(user, course_id):
    """
    Return corresponding string if user has staff or instructor role in Studio.
    This will not return student role because its purpose for using in Studio.

    :param course_id: the course_id of the course we're interested in
    """
    if auth.has_access(user, CourseInstructorRole(course_id)):
        return 'instructor'
    else:
        return 'staff'
