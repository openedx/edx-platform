"""
Asynchronous tasks for the LTI provider app.
"""

from django.conf import settings
from django.contrib.auth.models import User
from django.dispatch import receiver
import logging

from lms.djangoapps.grades import progress
from lms.djangoapps.grades.signals import SCORE_CHANGED
from lms import CELERY_APP
from lti_provider.models import GradedAssignment
import lti_provider.outcomes as outcomes
from lti_provider.views import parse_course_and_usage_keys
from opaque_keys.edx.keys import CourseKey
from xmodule.modulestore.django import modulestore

log = logging.getLogger("edx.lti_provider")


@receiver(SCORE_CHANGED)
def score_changed_handler(sender, **kwargs):  # pylint: disable=unused-argument
    """
    Consume signals that indicate score changes. See the definition of
    SCORE_CHANGED for a description of the signal.
    """
    points_possible = kwargs.get('points_possible', None)
    points_earned = kwargs.get('points_earned', None)
    user_id = kwargs.get('user_id', None)
    course_id = kwargs.get('course_id', None)
    usage_id = kwargs.get('usage_id', None)

    if None not in (points_earned, points_possible, user_id, course_id, user_id):
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


@CELERY_APP.task(name='lti_provider.tasks.send_composite_outcome')
def send_composite_outcome(user_id, course_id, assignment_id, version):
    """
    Calculate and transmit the score for a composite module (such as a
    vertical).

    A composite module may contain multiple problems, so we need to
    calculate the total points earned and possible for all child problems. This
    requires calculating the scores for the whole course, which is an expensive
    operation.

    Callers should be aware that the score calculation code accesses the latest
    scores from the database. This can lead to a race condition between a view
    that updates a user's score and the calculation of the grade. If the Celery
    task attempts to read the score from the database before the view exits (and
    its transaction is committed), it will see a stale value. Care should be
    taken that this task is not triggered until the view exits.

    The GradedAssignment model has a version_number field that is incremented
    whenever the score is updated. It is used by this method for two purposes.
    First, it allows the task to exit if it detects that it has been superseded
    by another task that will transmit the score for the same assignment.
    Second, it prevents a race condition where two tasks calculate different
    scores for a single assignment, and may potentially update the campus LMS
    in the wrong order.
    """
    assignment = GradedAssignment.objects.get(id=assignment_id)
    if version != assignment.version_number:
        log.info(
            "Score passback for GradedAssignment %s skipped. More recent score available.",
            assignment.id
        )
        return
    course_key = CourseKey.from_string(course_id)
    mapped_usage_key = assignment.usage_key.map_into_course(course_key)
    user = User.objects.get(id=user_id)
    course = modulestore().get_course(course_key, depth=0)
    progress_summary = progress.summary(user, course)
    earned, possible = progress_summary.score_for_module(mapped_usage_key)
    if possible == 0:
        weighted_score = 0
    else:
        weighted_score = float(earned) / float(possible)

    assignment = GradedAssignment.objects.get(id=assignment_id)
    if assignment.version_number == version:
        outcomes.send_score_update(assignment, weighted_score)


@CELERY_APP.task
def send_leaf_outcome(assignment_id, points_earned, points_possible):
    """
    Calculate and transmit the score for a single problem. This method assumes
    that the individual problem was the source of a score update, and so it
    directly takes the points earned and possible values. As such it does not
    have to calculate the scores for the course, making this method far faster
    than send_outcome_for_composite_assignment.
    """
    assignment = GradedAssignment.objects.get(id=assignment_id)
    if points_possible == 0:
        weighted_score = 0
    else:
        weighted_score = float(points_earned) / float(points_possible)
    outcomes.send_score_update(assignment, weighted_score)
