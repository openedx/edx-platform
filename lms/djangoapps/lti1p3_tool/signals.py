"""
Signals handlers for the lti_provider Django app.
"""
from __future__ import absolute_import
import logging

from django.dispatch import receiver
from lms.djangoapps.grades.api import signals as grades_signals
from .tasks import Lti1p3ScoresService

log = logging.getLogger(__name__)


@receiver(grades_signals.PROBLEM_WEIGHTED_SCORE_CHANGED)
def score_changed_handler(sender, **kwargs):  # pylint: disable=unused-argument
    """
    Consume signals that indicate score changes. See the definition of
    PROBLEM_WEIGHTED_SCORE_CHANGED for a description of the signal.
    """
    scores = Lti1p3ScoresService()
    scores.score_changed_handler(**kwargs)
