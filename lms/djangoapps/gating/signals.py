"""
Signal handlers for the gating djangoapp
"""
from django.db import models
from django.dispatch import receiver

from completion.models import BlockCompletion
from gating import api as gating_api
from gating.tasks import task_evaluate_subsection_completion_milestones
from lms.djangoapps.grades.signals.signals import SUBSECTION_SCORE_CHANGED
from openedx.core.djangoapps.signals.signals import COURSE_GRADE_CHANGED


@receiver(SUBSECTION_SCORE_CHANGED)
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
    course_id = unicode(instance.course_key)
    block_id = unicode(instance.block_key)
    user_id = instance.user_id
    task_evaluate_subsection_completion_milestones(course_id, block_id, user_id)


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
