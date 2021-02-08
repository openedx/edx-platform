from django.contrib.auth.models import User
from celery.task import task
from student.models import (
    CourseEnrollmentAllowed,
    CourseEnrollment,
    ManualEnrollmentAudit,
    ALLOWEDTOENROLL_TO_ENROLLED
)


@task()
def task_enroll_user_in_pending_courses(data):
    user = User.objects.get(id=data['user_id'])
    ceas = CourseEnrollmentAllowed.for_user(user).filter(auto_enroll=True)

    for cea in ceas:
        enrollment = CourseEnrollment.enroll(user, cea.course_id)
        manual_enrollment_audit = ManualEnrollmentAudit.get_manual_enrollment_by_email(user.email)
        if manual_enrollment_audit is not None:
            # get the enrolled by user and reason from the ManualEnrollmentAudit table.
            # then create a new ManualEnrollmentAudit table entry for the same email
            # different transition state.
            ManualEnrollmentAudit.create_manual_enrollment_audit(
                manual_enrollment_audit.enrolled_by,
                user.email,
                ALLOWEDTOENROLL_TO_ENROLLED,
                manual_enrollment_audit.reason,
                enrollment
            )
