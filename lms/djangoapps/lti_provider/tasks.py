"""
Asynchronous tasks for the LTI provider app.
"""

from django.dispatch import receiver
import logging

from courseware.models import SCORE_CHANGED
from lms import CELERY_APP
import lti_provider.outcomes as outcomes
from lti_provider.views import parse_course_and_usage_keys
from xmodule.modulestore.django import modulestore

log = logging.getLogger("edx.lti_provider")


@receiver(SCORE_CHANGED)
def score_changed_handler(sender, **kwargs):  # pylint: disable=unused-argument
    """
    Consume signals that indicate score changes. See the definition of
    courseware.models.SCORE_CHANGED for a description of the signal.
    """
    points_possible = kwargs.get('points_possible', None)
    points_earned = kwargs.get('points_earned', None)
    user_id = kwargs.get('user_id', None)
    course_id = kwargs.get('course_id', None)
    usage_id = kwargs.get('usage_id', None)

    if None not in (points_earned, points_possible, user_id, course_id, user_id):
        send_outcome.delay(
            points_possible,
            points_earned,
            user_id,
            course_id,
            usage_id
        )
    else:
        log.error(
            "Outcome Service: Required signal parameter is None. "
            "points_possible: %s, points_earned: %s, user_id: %s, "
            "course_id: %s, usage_id: %s",
            points_possible, points_earned, user_id, course_id, usage_id
        )


@CELERY_APP.task
def send_outcome(points_possible, points_earned, user_id, course_id, usage_id):
    """
    Calculate the score for a given user in a problem and send it to the
    appropriate LTI consumer's outcome service. This may involve sending
    multiple score updates, depending on what LTI requests have been received.
    """
    course_key, usage_key = parse_course_and_usage_keys(course_id, usage_id)
    problem_descriptor = modulestore().get_item(usage_key)

    # Get all assignments involving the current problem for which the campus LMS
    # is expecting a grade. There may be many possible graded assignments, if
    # a problem has been added several times to a course at different
    # granularities (such as the unit or the vertical).
    assignments = outcomes.get_assignments_for_problem(
        problem_descriptor, user_id, course_key
    )

    # Dictionary to hold the scores for each assignment. We already know the
    # score for the problem that triggered this task.
    scores = {usage_key: float(points_earned) / float(points_possible)}

    # To find the score for a composite block (such as a vertical) we need to
    # calculate the scores for the course. This is expensive, so we try to
    # short-circuit it if we can. In the case where the graded launch contained
    # only a single problem, and that problem is not a part of any other graded
    # assignment, we can just use the score passed to this method by the signal
    # handler.
    if len(assignments) != 1 or problem_descriptor not in assignments:
        # This is not the short-circuit case, so we need to calculate the score
        # for at least one composite block. We do this by calculating the scores
        # for all problems in the course, and then combining them to make up the
        # composite score.
        location_to_score = outcomes.get_scores_for_locations(
            user_id, course_key
        )
        for descriptor in assignments:
            # A location could be part of multiple graded assignments
            if descriptor.location not in scores:
                earned, possible = outcomes.calculate_score(
                    descriptor, location_to_score
                )
                if possible == 0:
                    score = 0
                else:
                    score = earned / possible
                scores[descriptor.location] = score

    # Send score updates to the campus LMS for all relevant assignments.
    for descriptor in assignments:
        for assignment in assignments[descriptor]:
            outcomes.send_score_update(assignment, scores[descriptor.location])
