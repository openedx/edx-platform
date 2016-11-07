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
from openedx.core.djangoapps.performance.utils import collect_profile_func
from xmodule.modulestore.django import modulestore

from .config.models import PersistentGradesEnabledFlag
from .new.subsection_grade import SubsectionGradeFactory
from .signals.signals import SUBSECTION_SCORE_CHANGED
from .transformer import GradesTransformer


@task(default_retry_delay=30, routing_key=settings.RECALCULATE_GRADES_ROUTING_KEY)
@collect_profile_func('recalculate_subsection_grade', enabled=False)
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
    if not PersistentGradesEnabledFlag.feature_enabled(course_key):
        return

    student = User.objects.get(id=user_id)
    scored_block_usage_key = UsageKey.from_string(usage_id).replace(course_key=course_key)

    course_structure = get_course_blocks(student, modulestore().make_course_usage_key(course_key))
    subsections_to_update = course_structure.get_transformer_block_field(
        scored_block_usage_key,
        GradesTransformer,
        'subsections',
        set(),
    )

    subsection_grade_factory = SubsectionGradeFactory(student, course_structure)
    try:
        for subsection_usage_key in subsections_to_update:
            subsection_grade = subsection_grade_factory.update(
                course_structure[subsection_usage_key],
                only_if_higher,
            )
            SUBSECTION_SCORE_CHANGED.send(
                sender=recalculate_subsection_grade,
                course_structure=course_structure,
                user=student,
                subsection_grade=subsection_grade,
            )

    except IntegrityError as exc:
        raise recalculate_subsection_grade.retry(args=[user_id, course_id, usage_id], exc=exc)
