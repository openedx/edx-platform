"""
API for the gating djangoapp
"""
from collections import defaultdict
from django.contrib.auth.models import User
from django.test.client import RequestFactory
import json
import logging

from openedx.core.lib.gating import api as gating_api
from opaque_keys.edx.keys import UsageKey
from lms.djangoapps.courseware.entrance_exams import get_entrance_exam_score
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
        course (CourseModule): The course
        prereq_content_key (UsageKey): The prerequisite content usage key
        user_id (int): ID of User for which evaluation should occur

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
                min_score = 100
                requirements = milestone.get('requirements')
                if requirements:
                    try:
                        min_score = int(requirements.get('min_score'))
                    except (ValueError, TypeError):
                        # Use default value of 100
                        pass

                if new_score >= min_score:
                    milestones_helpers.add_user_milestone({'id': user.id}, prereq_milestone)
                else:
                    milestones_helpers.remove_user_milestone({'id': user.id}, prereq_milestone)


def evaluate_entrance_exam(course, block, user_id):
    """
    Update milestone fulfillments for the specified content module
    """
    # Fulfillment Use Case: Entrance Exam
    # If this module is part of an entrance exam, we'll need to see if the student
    # has reached the point at which they can collect the associated milestone
    if milestones_helpers.is_entrance_exams_enabled():
        entrance_exam_enabled = getattr(course, 'entrance_exam_enabled', False)
        in_entrance_exam = getattr(block, 'in_entrance_exam', False)
        if entrance_exam_enabled and in_entrance_exam:
            # We don't have access to the true request object in this context, but we can use a mock
            request = RequestFactory().request()
            request.user = User.objects.get(id=user_id)
            exam_pct = get_entrance_exam_score(request, course)
            if exam_pct >= course.entrance_exam_minimum_score_pct:
                exam_key = UsageKey.from_string(course.entrance_exam_id)
                relationship_types = milestones_helpers.get_milestone_relationship_types()
                content_milestones = milestones_helpers.get_course_content_milestones(
                    course.id,
                    exam_key,
                    relationship=relationship_types['FULFILLS']
                )
                # Add each milestone to the user's set...
                user = {'id': request.user.id}
                for milestone in content_milestones:
                    milestones_helpers.add_user_milestone(user, milestone)
