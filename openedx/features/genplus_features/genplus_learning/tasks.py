import logging
from datetime import datetime
import pytz

from django.core.exceptions import ObjectDoesNotExist
from celery import shared_task
from edx_django_utils.monitoring import set_code_owner_attribute
from celery_utils.logged_task import LoggedTask
from celery_utils.persist_on_failure import LoggedPersistOnFailureTask

from opaque_keys.edx.keys import UsageKey, CourseKey
from completion.models import BlockCompletion
from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.course_modes.models import CourseMode
from openedx.features.genplus_features.genplus.models import Class
from openedx.features.genplus_features.genplus_learning.models import (
    Program, ProgramEnrollment, UnitCompletion, UnitBlockCompletion
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
    all_students = gen_class.students.select_related('gen_user').all()
    enrolled_students = ProgramEnrollment.objects\
                            .filter(program=program, student__in=all_students)\
                            .values_list('student', flat=True)
    unenrolled_students = all_students.exclude(pk__in=enrolled_students)

    if program_unit_ids:
        units = units.filter(program__in=program_unit_ids)

    if class_student_ids:
        unenrolled_students = unenrolled_students.filter(pk__in=class_student_ids)

    if not unenrolled_students:
        return

    program_enrollments = [
        ProgramEnrollment(
            student=student,
            program=program,
            gen_class=gen_class,
            status=ProgramEnrollmentStatuses.PENDING
        )
        for student in unenrolled_students
    ]
    ProgramEnrollment.objects.bulk_create(program_enrollments)

    unit_ids = units.values_list('course', flat=True)
    courses = []
    if program.intro_unit:
        courses.append(program.intro_unit)

    if program.outro_unit:
        courses.append(program.outro_unit)

    courses += [unit.course for unit in units]

    for student in unenrolled_students:
        if student.gen_user.user:
            for course in courses:
                course_enrollment, created = CourseEnrollment.objects.get_or_create(
                    user=student.gen_user.user, course=course, mode=CourseMode.AUDIT
                )

            ProgramEnrollment.objects.filter(program=program, student=student).update(status=ProgramEnrollmentStatuses.ENROLLED)
            log.info("Program and Unit Enrollments successfully created for student: %s", student)


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
def update_unit_and_lesson_completions(self, user_id, course_key_str, usage_key_str):
    usage_key = UsageKey.from_string(usage_key_str)
    block_type = usage_key.block_type
    aggregator_types = ['course', 'chapter', 'sequential', 'vertical']

    if block_type not in aggregator_types:
        course_key = CourseKey.from_string(course_key_str)
        block_id = usage_key.block_id
        user = User.objects.get(id=user_id)
        course_completion = get_course_completion(course_key_str, user, ['course'], block_id)

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
            user=user, course_key=course_key,
            defaults=defaults
        )

        for block in course_completion['children']:
            if block['attempted']:
                progress, is_complete = get_progress_and_completion_status(
                    block.get('total_completed_blocks'),
                    block.get('total_blocks')
                )
                block_usage_key = UsageKey.from_string(block['id'])
                defaults = {
                    'progress': progress,
                    'is_complete': is_complete,
                    'block_type': block.get('block_type'),
                }
                if is_complete:
                    defaults['completion_date'] = datetime.now().replace(tzinfo=pytz.UTC)

                UnitBlockCompletion.objects.update_or_create(
                    user=user, course_key=course_key, usage_key=block_usage_key,
                    defaults=defaults
                )
                return
