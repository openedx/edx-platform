"""
Tests for video outline API
"""


from courseware import access
from student.roles import CourseBetaTesterRole
from student import auth


def mobile_available_when_enrolled(course, user):
    """
    Determines whether a user has access to a course in a mobile context.
    Checks if the course is marked as mobile_available or the user has extra permissions
    that gives them access anyway.
    Does not check if the user is actually enrolled in the course
    """

    # The course doesn't always really exist -- we can have bad data in the enrollments
    # pointing to non-existent (or removed) courses, in which case `course` is None.
    if not course:
        return None

    # Implicitly includes instructor role via the following has_access check
    beta_tester_role = CourseBetaTesterRole(course.id)

    return (
        course.mobile_available
        or auth.has_access(user, beta_tester_role)
        or access.has_access(user, 'staff', course)
    )
