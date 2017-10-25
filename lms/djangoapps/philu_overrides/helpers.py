from openedx.core.djangoapps.models.course_details import CourseDetails
from courseware.courses import get_course_by_id

def get_course_details(course_id):
    course_descriptor = get_course_by_id(course_id)
    course = CourseDetails.populate(course_descriptor)

    return course
