from __future__ import absolute_import

import datetime
import logging

from django.conf import settings
from pylti1p3.grade import Grade
from pylti1p3.exception import LtiException
from lms import CELERY_APP
from lti_provider.tasks import ScoresService
from .models import GradedAssignment
from .message_launch import ExtendedDjangoMessageLaunch
from .tool_conf import ToolConfDb

log = logging.getLogger(__name__)


class Lti1p3ScoresService(ScoresService):

    def get_assignments_for_problem(self, descriptor, user_id, course_key):
        locations = []
        current_descriptor = descriptor
        while current_descriptor:
            locations.append(current_descriptor.location)
            current_descriptor = current_descriptor.get_parent()
        assignments = GradedAssignment.objects.filter(
            user=user_id, course_key=course_key, usage_key__in=locations
        )
        return assignments

    def start_send_leaf_outcome_task(self, assignment, points_earned, points_possible):
        lti1p3_send_leaf_outcome.delay(
            assignment.id, points_earned, points_possible
        )

    def start_send_composite_outcome_task(self, user_id, course_id, assignment):
        lti1p3_send_composite_outcome.apply_async(
            (user_id, course_id, assignment.id, assignment.version_number),
            countdown=settings.LTI_AGGREGATE_SCORE_PASSBACK_DELAY
        )

    def get_graded_assignment(self, assignment_id):
        return GradedAssignment.objects.get(id=assignment_id)

    def send_score(self, assignment, weighted_score):
        launch_data = {
            'iss': assignment.lti_tool.issuer,
            'aud': assignment.lti_tool.client_id,
            'https://purl.imsglobal.org/spec/lti-ags/claim/endpoint': assignment.lti_jwt_endpoint
        }
        tool_conf = ToolConfDb()

        try:
            message_launch = ExtendedDjangoMessageLaunch(request=None, tool_config=tool_conf)
            message_launch.set_auto_validation(enable=False)\
                .set_jwt({'body': launch_data})\
                .set_restored()\
                .validate_registration()

            ags = message_launch.get_ags()

            line_item = ags.find_lineitem_by_id(assignment.lti_lineitem)
            if not line_item:
                log.error("Lineitem %s isn't found in the external LMS", assignment.lti_lineitem)
                return

            timestamp = datetime.datetime.utcnow().isoformat()

            gr = Grade()
            gr.set_score_given(weighted_score)\
                .set_score_maximum(1)\
                .set_timestamp(timestamp)\
                .set_activity_progress('Submitted')\
                .set_grading_progress('FullyGraded')\
                .set_user_id(assignment.lti_jwt_sub)

            ags.put_grade(gr, line_item)
        except LtiException as e:
            log.exception("Error when sending grades to the LTI1.3 Platform: %s", str(e))


@CELERY_APP.task(name='lti1p3_tool.tasks.send_composite_outcome')
def lti1p3_send_composite_outcome(user_id, course_id, assignment_id, version):
    scores = Lti1p3ScoresService()
    scores.send_composite_outcome(user_id, course_id, assignment_id, version)


@CELERY_APP.task
def lti1p3_send_leaf_outcome(assignment_id, points_earned, points_possible):
    scores = Lti1p3ScoresService()
    scores.send_leaf_outcome(assignment_id, points_earned, points_possible)
