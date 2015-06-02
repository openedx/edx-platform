"""
Asynchronous tasks for the LTI provider app.
"""

from django.dispatch import receiver
import logging
from requests.exceptions import RequestException

from courseware.models import SCORE_CHANGED
from lms import CELERY_APP
from lti_provider.models import GradedAssignment
import lti_provider.outcomes
from lti_provider.views import parse_course_and_usage_keys

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
    appropriate LTI consumer's outcome service.
    """
    course_key, usage_key = parse_course_and_usage_keys(course_id, usage_id)
    assignments = GradedAssignment.objects.filter(
        user=user_id, course_key=course_key, usage_key=usage_key
    )

    # Calculate the user's score, on a scale of 0.0 - 1.0.
    score = float(points_earned) / float(points_possible)

    # There may be zero or more assignment records. We would expect for there
    # to be zero if the user/course/usage combination does not relate to a
    # previous graded LTI launch. This can happen if an LTI consumer embeds some
    # gradable content in a context that doesn't require a score (maybe by
    # including an exercise as a sample that students may complete but don't
    # count towards their grade).
    # There could be more than one GradedAssignment record if the same content
    # is embedded more than once in a single course. This would be a strange
    # course design on the consumer's part, but we handle it by sending update
    # messages for all launches of the content.
    for assignment in assignments:
        xml = lti_provider.outcomes.generate_replace_result_xml(
            assignment.lis_result_sourcedid, score
        )
        try:
            response = lti_provider.outcomes.sign_and_send_replace_result(assignment, xml)
        except RequestException:
            # failed to send result. 'response' is None, so more detail will be
            # logged at the end of the method.
            response = None
            log.exception("Outcome Service: Error when sending result.")

        # If something went wrong, make sure that we have a complete log record.
        # That way we can manually fix things up on the campus system later if
        # necessary.
        if not (response and lti_provider.outcomes.check_replace_result_response(response)):
            log.error(
                "Outcome Service: Failed to update score on LTI consumer. "
                "User: %s, course: %s, usage: %s, score: %s, possible: %s "
                "status: %s, body: %s",
                user_id,
                course_key,
                usage_key,
                points_earned,
                points_possible,
                response,
                response.text if response else 'Unknown'
            )
