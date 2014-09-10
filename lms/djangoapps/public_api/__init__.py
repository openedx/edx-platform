from xmodule.modulestore.django import modulestore
from rest_framework.exceptions import PermissionDenied

def get_mobile_course(course_id):
    """
    Return only courses that have mobile_available set to True
    """
    course = modulestore().get_course(course_id, depth=4)

    if not course.mobile_available:
        raise PermissionDenied(detail="Course not available on mobile.")
    return course
