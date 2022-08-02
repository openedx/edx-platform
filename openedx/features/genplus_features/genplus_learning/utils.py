import statistics

from django.conf import settings
from django.apps import apps
from openedx.core.lib.gating.api import get_subsection_completion_percentage
from lms.djangoapps.courseware.courses import get_course_blocks_completion_summary
from openedx.features.course_experience.utils import get_course_outline_block_tree
from xmodule.modulestore.django import modulestore
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview


def get_lesson_progress(section_usage_key, user):
    section_block = modulestore().get_item(section_usage_key)
    subsection_blocks = section_block.children
    percentages = [
        get_subsection_completion_percentage(block_usage_key, user)
        for block_usage_key in subsection_blocks
    ]
    return round(statistics.fmean(percentages)) if percentages else 0


def get_unit_progress(course_key, user):
    completion_summary = get_course_blocks_completion_summary(course_key, user)
    if completion_summary:
        total_count = completion_summary['complete_count'] + completion_summary['incomplete_count']
        return round((completion_summary['complete_count'] / total_count) * 100) if total_count else 0


def get_class_lesson_progress(section_usage_key, gen_class):
    percentages = []
    for student in gen_class.students.all():
        percentages.append(get_lesson_progress(section_usage_key, student.gen_user.user))

    return round(statistics.fmean(percentages)) if percentages else 0


def get_class_unit_progress(course_key, gen_class):
    percentages = []
    for student in gen_class.students.all():
        percentages.append(get_unit_progress(course_key, student.gen_user.user))

    return round(statistics.fmean(percentages)) if percentages else 0
