"""
API for the gating djangoapp
"""
from collections import defaultdict
from django.test.client import RequestFactory
import json
import logging

from lms.djangoapps.courseware.entrance_exams import get_entrance_exam_score
from openedx.core.lib.gating import api as gating_api
from opaque_keys.edx.keys import UsageKey
from xmodule.modulestore.django import modulestore
from util import milestones_helpers


log = logging.getLogger(__name__)


@gating_api.gating_enabled(default=False)
def evaluate_prerequisite(course, subsection_grade, user):
    """
    Evaluates any gating milestone relationships attached to the given
    subsection. If the subsection_grade meets the minimum score required
    by dependent subsections, the related milestone will be marked
    fulfilled for the user.
    """
    prereq_milestone = gating_api.get_gating_milestone(course.id, subsection_grade.location, 'fulfills')
    if prereq_milestone:
        gated_content_milestones = defaultdict(list)
        for milestone in gating_api.find_gating_milestones(course.id, content_key=None, relationship='requires'):
            gated_content_milestones[milestone['id']].append(milestone)

        gated_content = gated_content_milestones.get(prereq_milestone['id'])
        if gated_content:
            for milestone in gated_content:
                min_percentage = _get_minimum_required_percentage(milestone)
                subsection_percentage = _get_subsection_percentage(subsection_grade)
                if subsection_percentage >= min_percentage:
                    milestones_helpers.add_user_milestone({'id': user.id}, prereq_milestone)
                else:
                    milestones_helpers.remove_user_milestone({'id': user.id}, prereq_milestone)


def _get_minimum_required_percentage(milestone):
    """
    Returns the minimum percentage requirement for the given milestone.
    """
    # Default minimum score to 100
    min_score = 100
    requirements = milestone.get('requirements')
    if requirements:
        try:
            min_score = int(requirements.get('min_score'))
        except (ValueError, TypeError):
            log.warning(
                'Failed to find minimum score for gating milestone %s, defaulting to 100',
                json.dumps(milestone)
            )
    return min_score


def _get_subsection_percentage(subsection_grade):
    """
    Returns the percentage value of the given subsection_grade.
    """
    if subsection_grade.graded_total.possible:
        return float(subsection_grade.graded_total.earned) / float(subsection_grade.graded_total.possible) * 100.0
    else:
        return 0


def evaluate_entrance_exam(course, subsection_grade, user):
    """
    Evaluates any entrance exam milestone relationships attached
    to the given subsection. If the subsection_grade meets the
    minimum score required, the dependent milestone will be marked
    fulfilled for the user.
    """
    if milestones_helpers.is_entrance_exams_enabled() and getattr(course, 'entrance_exam_enabled', False):
        subsection = modulestore().get_item(subsection_grade.location)
        in_entrance_exam = getattr(subsection, 'in_entrance_exam', False)
        if in_entrance_exam:
            # We don't have access to the true request object in this context, but we can use a mock
            request = RequestFactory().request()
            request.user = user
            exam_pct = get_entrance_exam_score(request, course)
            if exam_pct >= course.entrance_exam_minimum_score_pct:
                exam_key = UsageKey.from_string(course.entrance_exam_id)
                relationship_types = milestones_helpers.get_milestone_relationship_types()
                content_milestones = milestones_helpers.get_course_content_milestones(
                    course.id,
                    exam_key,
                    relationship=relationship_types['FULFILLS']
                )
                # Mark each milestone dependent on the entrance exam as fulfilled by the user.
                for milestone in content_milestones:
                    milestones_helpers.add_user_milestone({'id': request.user.id}, milestone)
