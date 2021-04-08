"""
Signal handlers for the gating djangoapp
"""
from completion.models import BlockCompletion
from django.db import models
from django.dispatch import receiver

from lms.djangoapps.gating import api as gating_api
from lms.djangoapps.gating.tasks import task_evaluate_subsection_completion_milestones
from lms.djangoapps.grades.api import signals as grades_signals
from openedx.core.djangoapps.signals.signals import COURSE_GRADE_CHANGED


@receiver(grades_signals.SUBSECTION_SCORE_CHANGED)
def evaluate_subsection_gated_milestones(**kwargs):
    """
    Receives the SUBSECTION_SCORE_CHANGED signal and triggers the
    evaluation of any milestone relationships which are attached
    to the subsection.

    Arguments:
        kwargs (dict): Contains user, course, course_structure, subsection_grade
    Returns:
        None
    """
    subsection_grade = kwargs['subsection_grade']
    gating_api.evaluate_prerequisite(kwargs['course'], subsection_grade, kwargs.get('user'))


@receiver(models.signals.post_save, sender=BlockCompletion)
def evaluate_subsection_completion_milestones(**kwargs):
    """
    Receives the BlockCompletion signal and triggers the
    evaluation of any milestone which can be completed.
    """
    instance = kwargs['instance']
    course_id = str(instance.context_key)
    if not instance.context_key.is_course:
        return  # Content in a library or some other thing that doesn't support milestones
    block_id = str(instance.block_key)
    user_id = instance.user_id
    task_evaluate_subsection_completion_milestones.delay(course_id, block_id, user_id)


@receiver(COURSE_GRADE_CHANGED)
def evaluate_course_gated_milestones(**kwargs):
    """
    Receives the COURSE_GRADE_CHANGED signal and triggers the
    evaluation of any milestone relationships which are attached
    to the course grade.

    Arguments:
        kwargs (dict): Contains user, course_grade
    Returns:
        None
    """
    gating_api.evaluate_entrance_exam(kwargs['course_grade'], kwargs.get('user'))
