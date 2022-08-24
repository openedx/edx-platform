import statistics

from django.conf import settings
from django.apps import apps
from django.test import RequestFactory

from xmodule.modulestore.django import modulestore
from openedx.features.course_experience.utils import get_course_outline_block_tree
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.features.genplus_features.genplus_learning.models import UnitCompletion, UnitBlockCompletion


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
