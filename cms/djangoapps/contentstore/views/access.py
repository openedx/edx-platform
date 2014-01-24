from ..utils import get_course_location_for_item
from xmodule.modulestore.locator import CourseLocator
from student.roles import CourseStaffRole, GlobalStaff
from student import auth


def has_course_access(user, location, role=CourseStaffRole):
    """
    Return True if user allowed to access this piece of data
    Note that the CMS permissions model is with respect to courses
    There is a super-admin permissions if user.is_staff is set
    Also, since we're unifying the user database between LMS and CAS,
    I'm presuming that the course instructor (formally known as admin)
    will not be in both INSTRUCTOR and STAFF groups, so we have to cascade our
    queries here as INSTRUCTOR has all the rights that STAFF do
    """
    if GlobalStaff().has_user(user):
        return True
    if not isinstance(location, CourseLocator):
        # this can be expensive if location is not category=='course'
        location = get_course_location_for_item(location)
    return auth.has_access(user, role(location))
