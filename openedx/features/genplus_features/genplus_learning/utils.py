import statistics
from django.conf import settings
from openedx.core.lib.gating.api import get_subsection_completion_percentage
from xmodule.modulestore.django import modulestore


def get_section_completion_percentage(section_usage_key, user):
    section_block = modulestore().get_item(section_usage_key)
    subsection_blocks = section_block.children
    percentages = [
        get_subsection_completion_percentage(block_usage_key, user)
        for block_usage_key in subsection_blocks
    ]
    return round(statistics.fmean(percentages), 2) if percentages else 0


def get_lms_link_for_unit(course_key):
    course = modulestore().get_course(course_key)
    course_key_str = str(course_key)
    sections = course.children
    if sections:
        usage_key_str = str(sections[0])
    else:
        usage_key_str = str(modulestore().make_course_usage_key(course_key))

    return f"{settings.LMS_ROOT_URL}/courses/{course_key_str}/jump_to/{usage_key_str}"


def is_unit_locked(course_key):
    from openedx.features.genplus_features.genplus_learning.models import Lesson

    lessons = Lesson.objects.filter(course_key=course_key)
    if lessons:
        return all([lesson.is_locked for lesson in lessons])

    return False
