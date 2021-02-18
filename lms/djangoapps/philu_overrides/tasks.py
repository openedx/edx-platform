"""
Tasks for `philu_overrides` app
"""
from celery.task import task
from django.contrib.auth.models import User

from student.models import ALLOWEDTOENROLL_TO_ENROLLED, CourseEnrollment, CourseEnrollmentAllowed, ManualEnrollmentAudit


@task()
def task_enroll_user_in_pending_courses(data):
    user = User.objects.get(id=data['user_id'])
    allowed_auto_enroll_course_enrollments = CourseEnrollmentAllowed.for_user(user).filter(auto_enroll=True)

    for allowed_auto_enroll_course_enrollment in allowed_auto_enroll_course_enrollments:
        enrollment = CourseEnrollment.enroll(user, allowed_auto_enroll_course_enrollment.course_id)
        manual_enrollment_audit = ManualEnrollmentAudit.get_manual_enrollment_by_email(user.email)
        if manual_enrollment_audit is not None:
            ManualEnrollmentAudit.create_manual_enrollment_audit(
                manual_enrollment_audit.enrolled_by,
                user.email,
                ALLOWEDTOENROLL_TO_ENROLLED,
                manual_enrollment_audit.reason,
                enrollment
            )
