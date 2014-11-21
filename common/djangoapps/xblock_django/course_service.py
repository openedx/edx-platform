"""
Support for converting a course to an XBlock course
"""
from xblock.reference.course_service import XBlockCourse, CourseService
from xmodule.modulestore.django import modulestore

def convert_course_to_xblock_course(course):
    """
    A function that returns an XBlockCourse from the current course
    """
    return XBlockCourse(
        id=course.id,
        display_name=course.display_name,
        org=course.org,
        number=course.number
    )


class DjangoXBlockCourseService(CourseService):
    """
    A course service that converts courses to XBlockCourse
    """
    def __init__(self, course_id, **kwargs):
        super(DjangoXBlockCourseService, self).__init__(**kwargs)
        self._course_id = course_id

    def get_current_course(self):
        course = modulestore().get_course(self._course_id, depth=0)
        return convert_course_to_xblock_course(course)
