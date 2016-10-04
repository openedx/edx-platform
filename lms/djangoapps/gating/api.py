"""
API for the gating djangoapp
"""
import logging
import json

from collections import defaultdict
from django.contrib.auth.models import User
from openedx.core.lib.gating import api as gating_api
from util import milestones_helpers

log = logging.getLogger(__name__)


@gating_api.gating_enabled(default=False)
def evaluate_prerequisite(course, user, subsection_usage_key, new_score):
    """
    Finds the parent subsection of the content in the course and evaluates
    any milestone relationships attached to that subsection. If the calculated
    grade of the prerequisite subsection meets the minimum score required by
    dependent subsections, the related milestone will be fulfilled for the user.

    Arguments:
        user (User): User for which evaluation should occur
        course (CourseModule): The course
        subsection_usage_key (UsageKey): Usage key of the updated subsection
        new_score (float): New score of the given subsection, in percentage.

    Returns:
        None
    """
    prereq_milestone = gating_api.get_gating_milestone(
        course.id,
        subsection_usage_key,
        'fulfills'
    )
    if prereq_milestone:
        gated_content_milestones = defaultdict(list)
        for milestone in gating_api.find_gating_milestones(course.id, None, 'requires'):
            gated_content_milestones[milestone['id']].append(milestone)

        gated_content = gated_content_milestones.get(prereq_milestone['id'])
        if gated_content:
            for milestone in gated_content:
                # Default minimum score to 100
                min_score = 100.0
                requirements = milestone.get('requirements')
                if requirements:
                    try:
                        min_score = float(requirements.get('min_score'))
                    except (ValueError, TypeError):
                        log.warning(
                            'Failed to find minimum score for gating milestone %s, defaulting to 100',
                            json.dumps(milestone)
                        )

                if new_score >= min_score:
                    milestones_helpers.add_user_milestone({'id': user.id}, prereq_milestone)
                else:
                    milestones_helpers.remove_user_milestone({'id': user.id}, prereq_milestone)
