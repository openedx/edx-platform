import logging

from django.core.exceptions import ObjectDoesNotExist
from celery import shared_task
from edx_django_utils.monitoring import set_code_owner_attribute
from celery_utils.logged_task import LoggedTask
from celery_utils.persist_on_failure import LoggedPersistOnFailureTask

from common.djangoapps.student.models import CourseEnrollment
from openedx.features.genplus_features.genplus.models import Class, Student
from .models import Program, ProgramEnrollment, ProgramUnitEnrollment
from .constants import ProgramEnrollmentStatuses

log = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
@set_code_owner_attribute
def enroll_class_students_to_program(self, class_id, program_id, class_student_ids=[], program_unit_ids=[]):
    try:
        gen_class = Class.objects.get(pk=class_id)
        program = Program.objects.get(pk=program_id)
    except ObjectDoesNotExist:
        log.info("Class or program id does not exist")
        return

    units = program.units.all()
    students = gen_class.students.select_related('gen_user').all()

    if program_unit_ids:
        units = units.filter(program__in=program_unit_ids)

    if class_student_ids:
        students = students.filter(pk__in=class_student_ids)

    for student in students:
        try:
            program_enrollment = ProgramEnrollment.objects.get(
                student=student,
                program=program
            )
        except ProgramEnrollment.DoesNotExist:
            program_enrollment = ProgramEnrollment.objects.create(
                student=student,
                program=program,
                gen_class=gen_class,
                status=ProgramEnrollmentStatuses.ENROLLED
            )
            log.info(f"Program enrollment created for student: {student}, class: {gen_class}, program: {program}")

        for unit in units:
            if CourseEnrollment.is_enrolled(student.gen_user.user, unit.course.id):
                log.error(f'Student: {student} is already enrolled to course: {unit}!')
                return

            unit_enrollment, created = ProgramUnitEnrollment.objects.get_or_create(
                program_enrollment=program_enrollment,
                course=unit.course,
            )

            if created:
                unit_enrollment.course_enrollment = CourseEnrollment.enroll(
                    user=student.gen_user.user,
                    course_key=unit.course.id,
                )
                unit_enrollment.save()
                log.info(f"Program unit enrollment created for student: {student}, course: {unit}, program :{program}")
