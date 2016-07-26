"""
API for the gating djangoapp
"""
import logging
import json

from collections import defaultdict
from django.contrib.auth.models import User
from xmodule.modulestore.django import modulestore
from milestones import api as milestones_api
from openedx.core.lib.gating import api as gating_api
from lms.djangoapps.grades.module_grades import get_module_score


log = logging.getLogger(__name__)


def _get_xblock_parent(xblock, category=None):
    """
    Returns the parent of the given XBlock. If an optional category is supplied,
    traverses the ancestors of the XBlock and returns the first with the
    given category.

    Arguments:
        xblock (XBlock): Get the parent of this XBlock
        category (str): Find an ancestor with this category (e.g. sequential)
    """
    parent = xblock.get_parent()
    if parent and category:
        if parent.category == category:
            return parent
        else:
            return _get_xblock_parent(parent, category)
    return parent


@gating_api.gating_enabled(default=False)
def evaluate_prerequisite(course, prereq_content_key, user_id):
    """
    Finds the parent subsection of the content in the course and evaluates
    any milestone relationships attached to that subsection. If the calculated
    grade of the prerequisite subsection meets the minimum score required by
    dependent subsections, the related milestone will be fulfilled for the user.

    Arguments:
        user_id (int): ID of User for which evaluation should occur
        course (CourseModule): The course
        prereq_content_key (UsageKey): The prerequisite content usage key

    Returns:
        None
    """
    xblock = modulestore().get_item(prereq_content_key)
    sequential = _get_xblock_parent(xblock, 'sequential')
    if sequential:
        prereq_milestone = gating_api.get_gating_milestone(
            course.id,
            sequential.location.for_branch(None),
            'fulfills'
        )
        if prereq_milestone:
            gated_content_milestones = defaultdict(list)
            for milestone in gating_api.find_gating_milestones(course.id, None, 'requires'):
                gated_content_milestones[milestone['id']].append(milestone)

            gated_content = gated_content_milestones.get(prereq_milestone['id'])
            if gated_content:
                user = User.objects.get(id=user_id)
                score = get_module_score(user, course, sequential) * 100
                for milestone in gated_content:
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

                    if score >= min_score:
                        milestones_api.add_user_milestone({'id': user_id}, prereq_milestone)
                    else:
                        milestones_api.remove_user_milestone({'id': user_id}, prereq_milestone)
