import statistics
from collections import defaultdict

from django.conf import settings
from django.apps import apps
from django.test import RequestFactory

from xmodule.modulestore.django import modulestore
from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.course_modes.models import CourseMode
from openedx.features.course_experience.utils import get_course_outline_block_tree
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.features.genplus_features.genplus.models import Student
from openedx.features.genplus_features.genplus_learning.models import (
    Program, ProgramEnrollment, ClassLesson, ClassUnit, UnitCompletion, UnitBlockCompletion
)
from openedx.features.genplus_features.genplus_learning.constants import ProgramEnrollmentStatuses
from openedx.features.genplus_features.genplus_learning.access import allow_access
from openedx.features.genplus_features.genplus_learning.roles import ProgramStaffRole


def calculate_class_lesson_progress(course_key, usage_key, gen_class):
    # there are no users in this class
    user_ids = gen_class.students.all().values_list('gen_user__user', flat=True)
    if not user_ids:
        return 0

    students_lesson_progress = UnitBlockCompletion.objects.filter(
        user__in=user_ids, course_key=course_key, usage_key=usage_key, block_type='chapter'
    ).values_list('progress', flat=True)
    # no user in this class has attempted this lesson
    if not students_lesson_progress:
        return 0

    count = user_ids.count() - students_lesson_progress.count()
    students_lesson_progress = list(students_lesson_progress)
    students_lesson_progress += [0 for i in range(count)]
    return round(statistics.fmean(students_lesson_progress))


def calculate_class_unit_progress(course_key, gen_class):
    user_ids = gen_class.students.all().values_list('gen_user__user', flat=True)
    # there are no users in this class
    if not user_ids:
        return 0

    students_unit_progress = UnitCompletion.objects.filter(
        user__in=user_ids, course_key=course_key
    ).values_list('progress', flat=True)
    # no user in this class has attempted this unit
    if not students_unit_progress:
        return 0

    count = user_ids.count() - students_unit_progress.count()
    students_unit_progress = list(students_unit_progress)
    students_unit_progress += [0 for i in range(count)]
    return round(statistics.fmean(students_unit_progress))


def get_course_completion(course_key, user, include_block_children, block_id=None, request=None):
    if request is None:
        request = RequestFactory().get(u'/')
        request.user = user

    course_outline_blocks = get_course_outline_block_tree(
        request, course_key, request.user
    )

    if not course_outline_blocks:
        return None

    completion = get_course_block_completion(
        course_outline_blocks,
        include_block_children,
        block_id
    )

    return completion


def get_course_block_completion(course_block, include_block_children, block_id=None):

    if course_block is None:
        return {
            'block_type': None,
            'total_blocks': 0,
            'total_completed_blocks': 0,
        }

    course_block_children = course_block.get('children')
    block_type = course_block.get('type')
    completion = {
        'id': course_block.get('id'),
        'block_type': block_type,
    }

    if not course_block_children:
        completion['attempted'] = block_id is not None and block_id == course_block.get('block_id')
        if course_block.get('complete'):
            completion['total_blocks'] = 1
            completion['total_completed_blocks'] = 1
        else:
            completion['total_blocks'] = 1
            completion['total_completed_blocks'] = 0
        return completion

    completion['total_blocks'] = 0
    completion['total_completed_blocks'] = 0
    if block_type in include_block_children:
        completion['children'] = []

    attempted = False
    for block in course_block_children:
        child_completion = get_course_block_completion(
            block,
            include_block_children,
            block_id
        )

        completion['total_blocks'] += child_completion['total_blocks']
        completion['total_completed_blocks'] += child_completion['total_completed_blocks']
        attempted = attempted or child_completion['attempted']

        if block_type in include_block_children:
            completion['children'].append(child_completion)

    completion['attempted'] = attempted
    return completion


def get_progress_and_completion_status(total_completed_blocks, total_blocks):
    progress = round((total_completed_blocks / total_blocks) * 100) if total_blocks else 0
    is_complete = total_blocks == total_completed_blocks if total_blocks else False
    return progress, is_complete


def update_class_lessons(course_key):
    # retrieve units for all classes with course_key
    class_units = ClassUnit.objects.filter(course_key=course_key)

    course = modulestore().get_course(course_key)
    new_lesson_usage_keys = set(course.children)  # children has list of section usage keys

    old_lessons = ClassLesson.objects.filter(course_key=course_key)
    old_lesson_usage_keys = set(old_lessons.values_list('usage_key', flat=True))

    # delete removed section_usage_keys records
    removed_usage_keys = old_lesson_usage_keys - new_lesson_usage_keys
    ClassLesson.objects.filter(course_key=course_key, usage_key__in=removed_usage_keys).delete()

    new_usage_keys = new_lesson_usage_keys - old_lesson_usage_keys
    new_class_lessons = [
        ClassLesson(class_unit=class_unit, course_key=course_key, usage_key=usage_key)
        for class_unit in class_units
        for usage_key in new_usage_keys
    ]

    # bulk create new class lessons
    ClassLesson.objects.bulk_create(new_class_lessons)
    # update lesson order
    for order, usage_key in enumerate(course.children, start=1):
        ClassLesson.objects.filter(course_key=course_key, usage_key=usage_key).update(order=order)


def get_absolute_url(request, file):
    return request.build_absolute_uri(file.url) if file else None


def process_pending_student_program_enrollments(gen_user):
    pending_enrollments = ProgramEnrollment.objects.filter(
                                student__gen_user=gen_user,
                                gen_class__isnull=False,
                                status=ProgramEnrollmentStatuses.PENDING)

    for program_enrollment in pending_enrollments:
        program = program_enrollment.program
        course_ids = list(program.units.all().values_list('course', flat=True))
        if program.intro_unit:
            course_ids.append(program.intro_unit.id)
        if program.outro_unit:
            course_ids.append(program.outro_unit.id)

        for course_id in course_ids:
            course_enrollment, created = CourseEnrollment.objects.get_or_create(
                course_id=course_id,
                user_id=gen_user.user.id,
                mode=CourseMode.AUDIT,
            )

        if CourseEnrollment.objects.filter(course_id__in=course_ids, user_id=gen_user.user.id).count() == len(course_ids):
            program_enrollment.status = ProgramEnrollmentStatuses.ENROLLED
            program_enrollment.save()
            Student.objects.filter(gen_user=gen_user).update(active_class=program_enrollment.gen_class)


def process_pending_teacher_program_access(gen_user):
    program_ids = gen_user.school.classes.exclude(program__isnull=True)\
                                        .values_list('program', flat=True)\
                                        .distinct()\
                                        .order_by()
    programs = Program.objects.filter(pk__in=program_ids)
    for program in programs:
        allow_access(program, gen_user, ProgramStaffRole.ROLE_NAME)
