"""
This module contains tasks for asynchronous execution of grade updates.
"""

from celery import task
from django.conf import settings
from django.contrib.auth.models import User
from django.db.utils import IntegrityError

from lms.djangoapps.course_blocks.api import get_course_blocks
from opaque_keys.edx.keys import UsageKey
from opaque_keys.edx.locator import CourseLocator
from openedx.core.djangoapps.content.block_structure.api import get_course_in_cache
from xmodule.modulestore.django import modulestore

from .config.models import PersistentGradesEnabledFlag
from .new.course_grade import CourseGradeFactory
from .new.subsection_grade import SubsectionGradeFactory
from .signals.signals import SUBSECTION_SCORE_CHANGED
from .transformer import GradesTransformer


@task(default_retry_delay=30, routing_key=settings.RECALCULATE_GRADES_ROUTING_KEY)
def recalculate_subsection_grade(user_id, course_id, usage_id, only_if_higher):
    """
    Updates a saved subsection grade.
    This method expects the following parameters:
       - user_id: serialized id of applicable User object
       - course_id: Unicode string representing the course
       - usage_id: Unicode string indicating the courseware instance
       - only_if_higher: boolean indicating whether grades should
        be updated only if the new grade is higher than the previous
        value.
    """
    course_key = CourseLocator.from_string(course_id)
    student = User.objects.get(id=user_id)
    scored_block_usage_key = UsageKey.from_string(usage_id).replace(course_key=course_key)

    collected_block_structure = get_course_in_cache(course_key)
    course = modulestore().get_course(course_key, depth=0)
    subsection_grade_factory = SubsectionGradeFactory(student, course, collected_block_structure)
    subsections_to_update = collected_block_structure.get_transformer_block_field(
        scored_block_usage_key,
        GradesTransformer,
        'subsections',
        set()
    )

    try:
        for subsection_usage_key in subsections_to_update:
            transformed_subsection_structure = get_course_blocks(
                student,
                subsection_usage_key,
                collected_block_structure=collected_block_structure,
            )
            subsection_grade = subsection_grade_factory.update(
                transformed_subsection_structure[subsection_usage_key],
                transformed_subsection_structure,
                only_if_higher,
            )
            SUBSECTION_SCORE_CHANGED.send(
                sender=recalculate_subsection_grade,
                course=course,
                user=student,
                subsection_grade=subsection_grade,
            )

    except IntegrityError as exc:
        raise recalculate_subsection_grade.retry(args=[user_id, course_id, usage_id], exc=exc)


@task(default_retry_delay=30, routing_key=settings.RECALCULATE_GRADES_ROUTING_KEY)
def recalculate_course_grade(user_id, course_id):
    """
    Updates a saved course grade.
    This method expects the following parameters:
       - user_id: serialized id of applicable User object
       - course_id: Unicode string representing the course
    """
    if not PersistentGradesEnabledFlag.feature_enabled(course_id):
        return
    student = User.objects.get(id=user_id)
    course_key = CourseLocator.from_string(course_id)
    course = modulestore().get_course(course_key, depth=0)

    try:
        CourseGradeFactory(student).update(course)
    except IntegrityError as exc:
        raise recalculate_course_grade.retry(args=[user_id, course_id], exc=exc)
