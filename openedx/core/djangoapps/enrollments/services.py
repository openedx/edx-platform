"""
Enrollments Service
"""


from common.djangoapps.student.models import CourseEnrollment


class EnrollmentsService(object):
    """
    Enrollments service

    Provides functions related to course enrollments
    """

    def get_active_enrollments_by_course(self, course_id):
        """
        Returns a list of active enrollments for a course
        """
        return list(CourseEnrollment.objects.filter(course_id=course_id, is_active=True))
