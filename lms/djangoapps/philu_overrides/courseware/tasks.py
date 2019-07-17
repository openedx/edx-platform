import json
import logging

from courseware.models import StudentModule
from django.contrib.auth.models import User
from celery.task import task
from common.djangoapps.student.models import (
                                CourseEnrollmentAllowed,
                                CourseEnrollment,
                                ManualEnrollmentAudit,
                                ALLOWEDTOENROLL_TO_ENROLLED
                            )


log = logging.getLogger('edx.celery.task')


def task_correct_polls_data():
    """
    This task method converts possible choices data from list to string
    :return:
    """
    log.info('Getting student modules')

    student_modules = StudentModule.objects.filter(state__icontains='possible_choices')
    for module in student_modules:
        user_state = module.state
        try:
            json_state = json.loads(user_state)
            json_possible_choices = json_state["possible_choices"]

            if type(json_possible_choices) is list:

                possible_choices = json.dumps(json_possible_choices)
                json_state.update({"possible_choices": possible_choices})

                module.state = json.dumps(json_state)
                module.save()

                log.info('Module changed with id ' + str(module.id))
        except Exception as ex:
            log.error('Code failed for ' + str(module.id) + ' and error is ' + str(ex.message))


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
