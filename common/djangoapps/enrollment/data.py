"""
Data Aggregation Layer of the Enrollment API. Collects all enrollment specific data into a single
source to be used throughout the API.

"""
from student.models import CourseEnrollment


def get_course_enrollments(student_id):
    qset = CourseEnrollment.objects.filter(
        user__username=student_id, is_active=True
    ).order_by('created')
    return qset


def get_course_enrollment(student_id, course_id):
    pass

def update_course_enrollment(student_id, course_id, enrollment):
    pass


def get_course_enrollment_info(course_id):
    pass


def get_course_enrollments_info(student_id):
    pass
    # qset = CourseDescriptor.objects.filter(
    #     user__username=student_id, is_active=True
    # ).order_by('created')
    # return qset
