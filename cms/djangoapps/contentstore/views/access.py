""" Helper methods for determining user access permissions in Studio """

from student.roles import CourseStaffRole, GlobalStaff, CourseInstructorRole, OrgStaffRole, OrgInstructorRole
from student import auth


def has_course_access(user, course_key, role=CourseStaffRole):
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
    if OrgInstructorRole(org=course_key.org).has_user(user):
        return True
    if OrgStaffRole(org=course_key.org).has_user(user):
        return True
    # temporary to ensure we give universal access given a course until we impl branch specific perms
    return auth.has_access(user, role(course_key.for_branch(None)))


def get_user_role(user, course_id):
    """
    What type of access: staff or instructor does this user have in Studio?

    No code should use this for access control, only to quickly serialize the type of access
    where this code knows that Instructor trumps Staff and assumes the user has one or the other.

    This will not return student role because its purpose for using in Studio.

    :param course_id: the course_id of the course we're interested in
    """
    # afaik, this is only used in lti
    if auth.has_access(user, CourseInstructorRole(course_id)):
        return 'instructor'
    else:
        return 'staff'
