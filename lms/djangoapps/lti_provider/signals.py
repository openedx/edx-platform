"""
Signals handlers for the lti_provider Django app.
"""
from __future__ import absolute_import
import logging

from django.conf import settings
from django.dispatch import receiver

import lti_provider.outcomes as outcomes
from lms.djangoapps.grades.signals.signals import PROBLEM_WEIGHTED_SCORE_CHANGED
from lti_provider.views import parse_course_and_usage_keys
from xmodule.modulestore.django import modulestore
from .tasks import send_composite_outcome, send_leaf_outcome

log = logging.getLogger(__name__)


def increment_assignment_versions(course_key, usage_key, user_id):
    """
    Update the version numbers for all assignments that are affected by a score
    change event. Returns a list of all affected assignments.
    """
    problem_descriptor = modulestore().get_item(usage_key)
    # Get all assignments involving the current problem for which the campus LMS
    # is expecting a grade. There may be many possible graded assignments, if
    # a problem has been added several times to a course at different
    # granularities (such as the unit or the vertical).
    assignments = outcomes.get_assignments_for_problem(
        problem_descriptor, user_id, course_key
    )
    for assignment in assignments:
        assignment.version_number += 1
        assignment.save()
    return assignments


@receiver(PROBLEM_WEIGHTED_SCORE_CHANGED)
def score_changed_handler(sender, **kwargs):  # pylint: disable=unused-argument
    """
    Consume signals that indicate score changes. See the definition of
    PROBLEM_WEIGHTED_SCORE_CHANGED for a description of the signal.
    """
    points_possible = kwargs.get('weighted_possible', None)
    points_earned = kwargs.get('weighted_earned', None)
    user_id = kwargs.get('user_id', None)
    course_id = kwargs.get('course_id', None)
    usage_id = kwargs.get('usage_id', None)

    if None not in (points_earned, points_possible, user_id, course_id):
        course_key, usage_key = parse_course_and_usage_keys(course_id, usage_id)
        assignments = increment_assignment_versions(course_key, usage_key, user_id)
        for assignment in assignments:
            if assignment.usage_key == usage_key:
                send_leaf_outcome.delay(
                    assignment.id, points_earned, points_possible
                )
            else:
                send_composite_outcome.apply_async(
                    (user_id, course_id, assignment.id, assignment.version_number),
                    countdown=settings.LTI_AGGREGATE_SCORE_PASSBACK_DELAY
                )
    else:
        log.error(
            "Outcome Service: Required signal parameter is None. "
            "points_possible: %s, points_earned: %s, user_id: %s, "
            "course_id: %s, usage_id: %s",
            points_possible, points_earned, user_id, course_id, usage_id
        )
