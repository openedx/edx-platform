"""
Signal handlers for the gating djangoapp
"""
from django.dispatch import receiver
from lms.djangoapps.grades.signals.signals import SUBSECTION_SCORE_UPDATED
from gating import api as gating_api


@receiver(SUBSECTION_SCORE_UPDATED)
def handle_subsection_score_updated(**kwargs):
    """
    Receives the SCORE_CHANGED signal sent by LMS when a student's score has changed
    for a given component and triggers the evaluation of any milestone relationships
    which are attached to the updated content.

    Arguments:
        kwargs (dict): Contains user ID, course key, and content usage key

    Returns:
        None
    """
    course = kwargs['course']
    if course.enable_subsection_gating:
        subsection_grade = kwargs['subsection_grade']
        new_score = subsection_grade.graded_total.earned / subsection_grade.graded_total.possible * 100.0
        gating_api.evaluate_prerequisite(
            course,
            kwargs['user'],
            subsection_grade.location,
            new_score,
        )
