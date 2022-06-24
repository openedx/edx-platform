import logging

from celery import shared_task
from edx_django_utils.monitoring import set_code_owner_attribute
from celery_utils.logged_task import LoggedTask
from celery_utils.persist_on_failure import LoggedPersistOnFailureTask

from common.djangoapps.student.models import CourseEnrollment, AlreadyEnrolledError
from openedx.features.genplus_features.genplus.models import Class
from .models import Program, ProgramEnrollment, ProgramUnitEnrollment
from .constants import ProgramEnrollmentStatuses

log = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
@set_code_owner_attribute
def enroll_class_students_to_program(self, **kwargs):
    gen_class_id = kwargs.get('gen_class_id')
    program_id = kwargs.get('program_id')

    if not (gen_class_id and program_id):
        log.info("Class or program id is not valid")
        return

    gen_class = Class.objects.get(pk=gen_class_id)
    program = Program.objects.get(pk=program_id)
    units = program.units.all()
    students = gen_class.students.select_related('gen_user').all()

    for student in students:
        program_enrollment, created = ProgramEnrollment.objects.get_or_create(
            student=student,
            from_class=gen_class,
            program=program,
        )

        if created:
            log.info(f"Program enrollment created for student: {student}, class: {gen_class}, program: {program}")
            program_enrollment.status = ProgramEnrollmentStatuses.ENROLLED
            program_enrollment.save()

        for unit in units:
            unit_enrollment, created = ProgramUnitEnrollment.objects.get_or_create(
                program_enrollment=program_enrollment,
                course_key=unit.id,
            )

            if created:
                try:
                    course_enrollment = CourseEnrollment.enroll(
                        user=student.gen_user.user,
                        course_key=unit.id,
                    )
                    unit_enrollment.course_enrollment = course_enrollment
                    unit_enrollment.save()
                    log.info(f"Program unit enrollment created for student: {student}, class: {gen_class}, course: {unit.id}, program :{program}")

                except AlreadyEnrolledError:
                    log.exception(f'Student: {student} from class: {gen_class}, is already enrolled to course: {unit.id}!')
