import logging
from datetime import datetime
import pytz

from django.core.exceptions import ObjectDoesNotExist
from celery import shared_task
from edx_django_utils.monitoring import set_code_owner_attribute
from celery_utils.logged_task import LoggedTask
from celery_utils.persist_on_failure import LoggedPersistOnFailureTask

from opaque_keys.edx.keys import UsageKey
from completion.models import BlockCompletion
from common.djangoapps.student.models import CourseEnrollment
from openedx.features.genplus_features.genplus.models import Class, Student
from openedx.features.genplus_features.genplus_learning.models import (
    Program, ProgramEnrollment, ProgramUnitEnrollment, UnitCompletion, UnitBlockCompletion
)
from openedx.features.genplus_features.genplus_learning.constants import ProgramEnrollmentStatuses
from openedx.features.genplus_features.genplus_learning.utils import (
    get_course_completion, get_progress_and_completion_status
)
from openedx.features.genplus_features.genplus_learning.access import allow_access
from openedx.features.genplus_features.genplus_learning.roles import ProgramStaffRole

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
                status=ProgramEnrollmentStatuses.PENDING
            )
            log.info(f"Program enrollment created for student: {student}, class: {gen_class}, program: {program}")

        for unit in units:
            if not student.user or CourseEnrollment.is_enrolled(student.gen_user.user, unit.course.id):
                log.error(f'User does not exist or Student: {student} is already enrolled to course: {unit}!')
                continue

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

        if units.count() == program_enrollment.program_unit_enrollments.all().count():
            program_enrollment.status = ProgramEnrollmentStatuses.ENROLLED
            program_enrollment.save()


@shared_task(
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
@set_code_owner_attribute
def allow_program_access_to_class_teachers(self, class_id, program_id, class_teacher_ids=[]):
    try:
        gen_class = Class.objects.get(pk=class_id)
        program = Program.objects.get(pk=program_id)
    except ObjectDoesNotExist:
        log.info("Class or program id does not exist")
        return

    teachers = gen_class.teachers.select_related('gen_user').exclude(gen_user__user__isnull=True)

    if class_teacher_ids:
        teachers = teachers.filter(pk__in=class_teacher_ids)

    for teacher in teachers:
        allow_access(program, teacher.gen_user, ProgramStaffRole.ROLE_NAME)


@shared_task(
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
@set_code_owner_attribute
def update_unit_and_lesson_completions(self, block_completion_id):
    try:
        block_completion = BlockCompletion.objects.get(pk=block_completion_id)
    except BlockCompletion.DoesNotExist:
        log.info("Block completion does not exist")
        return

    block_type = block_completion.block_type
    aggregator_types = ['course', 'chapter', 'sequential', 'vertical']
    if block_type not in aggregator_types:
        course_key = str(block_completion.context_key)
        if not block_completion.context_key.is_course:
            return

        block_id = block_completion.block_key.block_id
        user = block_completion.user
        course_completion = get_course_completion(course_key, user, ['course'], block_id)

        if not (course_completion and course_completion.get('attempted')):
            return

        progress, is_complete = get_progress_and_completion_status(
            course_completion.get('total_completed_blocks'),
            course_completion.get('total_blocks')
        )
        defaults = {
            'progress': progress,
            'is_complete': is_complete,
        }
        if is_complete:
            defaults['completion_date'] = datetime.now().replace(tzinfo=pytz.UTC)

        UnitCompletion.objects.update_or_create(
            user=user, course_key=block_completion.context_key,
            defaults=defaults
        )

        for block in course_completion['children']:
            if block['attempted']:
                progress, is_complete = get_progress_and_completion_status(
                    block.get('total_completed_blocks'),
                    block.get('total_blocks')
                )
                usage_key = UsageKey.from_string(block['id'])
                defaults = {
                    'progress': progress,
                    'is_complete': is_complete,
                    'block_type': block.get('block_type'),
                }
                if is_complete:
                    defaults['completion_date'] = datetime.now().replace(tzinfo=pytz.UTC)

                UnitBlockCompletion.objects.update_or_create(
                    user=user, course_key=block_completion.context_key, usage_key=usage_key,
                    defaults=defaults
                )
                return
