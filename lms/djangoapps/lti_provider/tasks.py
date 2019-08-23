"""
Asynchronous tasks for the LTI provider app.
"""

from __future__ import absolute_import

import logging

from django.conf import settings
from django.contrib.auth.models import User
from opaque_keys.edx.keys import CourseKey

import lti_provider.outcomes as outcomes
from lms import CELERY_APP
from lms.djangoapps.grades.api import CourseGradeFactory
from lti_provider.models import GradedAssignment
from lti_provider.views import parse_course_and_usage_keys
from xmodule.modulestore.django import modulestore

log = logging.getLogger(__name__)


class ScoresService(object):

    def get_assignments_for_problem(self, descriptor, user_id, course_key):
        return outcomes.get_assignments_for_problem(
            descriptor, user_id, course_key
        )

    def increment_assignment_versions(self, course_key, usage_key, user_id):
        """
        Update the version numbers for all assignments that are affected by a score
        change event. Returns a list of all affected assignments.
        """
        problem_descriptor = modulestore().get_item(usage_key)
        # Get all assignments involving the current problem for which the campus LMS
        # is expecting a grade. There may be many possible graded assignments, if
        # a problem has been added several times to a course at different
        # granularities (such as the unit or the vertical).
        assignments = self.get_assignments_for_problem(
            problem_descriptor, user_id, course_key
        )
        for assignment in assignments:
            assignment.version_number += 1
            assignment.save()
        return assignments

    def start_send_leaf_outcome_task(self, assignment, points_earned, points_possible):
        send_leaf_outcome.delay(
            assignment.id, points_earned, points_possible
        )

    def start_send_composite_outcome_task(self, user_id, course_id, assignment):
        send_composite_outcome.apply_async(
            (user_id, course_id, assignment.id, assignment.version_number),
            countdown=settings.LTI_AGGREGATE_SCORE_PASSBACK_DELAY
        )

    def score_changed_handler(self, **kwargs):
        points_possible = kwargs.get('weighted_possible', None)
        points_earned = kwargs.get('weighted_earned', None)
        user_id = kwargs.get('user_id', None)
        course_id = kwargs.get('course_id', None)
        usage_id = kwargs.get('usage_id', None)

        if None not in (points_earned, points_possible, user_id, course_id):
            course_key, usage_key = parse_course_and_usage_keys(course_id, usage_id)
            assignments = self.increment_assignment_versions(course_key, usage_key, user_id)
            for assignment in assignments:
                if assignment.usage_key == usage_key:
                    self.start_send_leaf_outcome_task(assignment, points_earned, points_possible)
                else:
                    self.start_send_composite_outcome_task(user_id, course_id, assignment)
        else:
            log.error(
                u"Outcome Service: Required signal parameter is None. "
                u"points_possible: %s, points_earned: %s, user_id: %s, "
                u"course_id: %s, usage_id: %s",
                points_possible, points_earned, user_id, course_id, usage_id
            )

    def get_graded_assignment(self, assignment_id):
        return GradedAssignment.objects.get(id=assignment_id)

    def send_score(self, assignment, weighted_score):
        outcomes.send_score_update(assignment, weighted_score)

    def send_composite_outcome(self, user_id, course_id, assignment_id, version):
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
        assignment = self.get_graded_assignment(assignment_id)
        if version != assignment.version_number:
            log.info(
                u"Score passback for GradedAssignment %s skipped. More recent score available.",
                assignment.id
            )
            return
        course_key = CourseKey.from_string(course_id)
        mapped_usage_key = assignment.usage_key.map_into_course(course_key)
        user = User.objects.get(id=user_id)
        course = modulestore().get_course(course_key, depth=0)
        course_grade = CourseGradeFactory().read(user, course)
        earned, possible = course_grade.score_for_module(mapped_usage_key)
        if possible == 0:
            weighted_score = 0
        else:
            weighted_score = float(earned) / float(possible)

        assignment = self.get_graded_assignment(assignment_id)
        if assignment.version_number == version:
            self.send_score(assignment, weighted_score)

    def send_leaf_outcome(self, assignment_id, points_earned, points_possible):
        """
        Calculate and transmit the score for a single problem. This method assumes
        that the individual problem was the source of a score update, and so it
        directly takes the points earned and possible values. As such it does not
        have to calculate the scores for the course, making this method far faster
        than send_outcome_for_composite_assignment.
        """
        assignment = self.get_graded_assignment(assignment_id)
        if points_possible == 0:
            weighted_score = 0
        else:
            weighted_score = float(points_earned) / float(points_possible)
        self.send_score(assignment, weighted_score)


@CELERY_APP.task(name='lti_provider.tasks.send_composite_outcome')
def send_composite_outcome(user_id, course_id, assignment_id, version):
    scores = ScoresService()
    scores.send_composite_outcome(user_id, course_id, assignment_id, version)


@CELERY_APP.task
def send_leaf_outcome(assignment_id, points_earned, points_possible):
    scores = ScoresService()
    scores.send_leaf_outcome(assignment_id, points_earned, points_possible)
