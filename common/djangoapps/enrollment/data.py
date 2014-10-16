"""
Data Aggregation Layer of the Enrollment API. Collects all enrollment specific data into a single
source to be used throughout the API.

"""
from django.contrib.auth.models import User
from opaque_keys.edx.keys import CourseKey
from enrollment.serializers import CourseEnrollmentSerializer
from student.models import CourseEnrollment


def get_course_enrollments(student_id):
    qset = CourseEnrollment.objects.filter(
        user__username=student_id, is_active=True
    ).order_by('created')
    return CourseEnrollmentSerializer(qset).data


def get_course_enrollment(student_id, course_id):
    course_key = CourseKey.from_string(course_id)
    try:
        enrollment = CourseEnrollment.objects.get(
            user__username=student_id, course_id=course_key
        )
        return CourseEnrollmentSerializer(enrollment).data
    except CourseEnrollment.DoesNotExist:
        return None


def update_course_enrollment(student_id, course_id, mode=None, is_active=None):
    course_key = CourseKey.from_string(course_id)
    student = User.objects.get(username=student_id)
    if not CourseEnrollment.is_enrolled(student, course_key):
        enrollment = CourseEnrollment.enroll(student, course_key)
    else:
        enrollment = CourseEnrollment.objects.get(user=student, course_id=course_key)

    enrollment.update_enrollment(is_active=is_active, mode=mode)
    enrollment.save()
    return CourseEnrollmentSerializer(enrollment).data


def get_course_enrollment_info(course_id):
    pass


def get_course_enrollments_info(student_id):
    pass
