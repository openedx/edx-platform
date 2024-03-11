""" Celery Tasks for the Instructor App. """

from datetime import datetime
import logging
from celery import shared_task
from submissions import api as sub_api
from edx_django_utils.monitoring import set_code_owner_attribute

from common.djangoapps.student.models.course_enrollment import CourseEnrollment
from common.djangoapps.student.models.user import get_user_by_username_or_email
from lms.djangoapps.courseware.courses import get_course
from lms.djangoapps.courseware.models import StudentModule
from lms.djangoapps.grades.rest_api.v1.views import SubmissionHistoryView
from lms.djangoapps.instructor.enrollment import reset_student_attempts
from lms.djangoapps.support.models import CourseResetAudit

log = logging.getLogger(__name__)


def update_audit_fields(audit_instance, status, completed_at=False):
    audit_instance.status = status
    if completed_at:
        audit_instance.completed_at = datetime.now()
    audit_instance.save()


@shared_task
@set_code_owner_attribute
def reset_student_course(course_id, learner_email, reset_by_user_email):
    """
    Resets a learner's course progress
    """
    user = get_user_by_username_or_email(learner_email)
    reset_by_user = get_user_by_username_or_email(reset_by_user_email)
    enrollment = CourseEnrollment.objects.get(
        course=course_id,
        user=user,
        is_active=True
    )
    course_overview = enrollment.course_overview
    course_reset_audit = CourseResetAudit.objects.filter(course_enrollment=enrollment).first()
    update_audit_fields(course_reset_audit, CourseResetAudit.CourseResetStatus.IN_PROGRESS)

    try:
        course = get_course(course_overview.id, depth=4)
        history = SubmissionHistoryView.get_problem_blocks(course)
        for data in history:
            try:
                reset_student_attempts(course.id, user, data.scope_ids.usage_id, reset_by_user, True)
            except StudentModule.DoesNotExist:
                pass
        update_audit_fields(course_reset_audit, CourseResetAudit.CourseResetStatus.COMPLETE, True)
    except sub_api.SubmissionError as e:
        logging.exception(e)
        update_audit_fields(course_reset_audit, CourseResetAudit.CourseResetStatus.FAILED)
