"""
Progress Summary of a learner's course grades.
"""
from course_blocks.api import get_course_blocks
from courseware.model_data import ScoresClient
from openedx.core.lib.gating import api as gating_api
from student.models import anonymous_id_for_user
from util.db import outer_atomic
from xmodule import graders, block_metadata_utils
from xmodule.graders import Score

from .scores import get_score, possibly_scored


class ProgressSummary(object):
    """
    Wrapper class for the computation of a user's scores across a course.

    Attributes
       chapters: a summary of all sections with problems in the course. It is
       organized as an array of chapters, each containing an array of sections,
       each containing an array of scores. This contains information for graded
       and ungraded problems, and is good for displaying a course summary with
       due dates, etc.

       weighted_scores: a dictionary mapping module locations to weighted Score
       objects.

       locations_to_children: a function mapping locations to their
       direct descendants.
    """
    def __init__(self, chapters=None, weighted_scores=None, locations_to_children=None):
        self.chapters = chapters
        self.weighted_scores = weighted_scores
        self.locations_to_children = locations_to_children

    def score_for_module(self, location):
        """
        Calculate the aggregate weighted score for any location in the course.
        This method returns a tuple containing (earned_score, possible_score).

        If the location is of 'problem' type, this method will return the
        possible and earned scores for that problem. If the location refers to a
        composite module (a vertical or section ) the scores will be the sums of
        all scored problems that are children of the chosen location.
        """
        if location in self.weighted_scores:
            score = self.weighted_scores[location]
            return score.earned, score.possible
        children = self.locations_to_children[location]
        earned = 0.0
        possible = 0.0
        for child in children:
            child_earned, child_possible = self.score_for_module(child)
            earned += child_earned
            possible += child_possible
        return earned, possible


def summary(student, course, course_structure=None):
    """
    This pulls a summary of all problems in the course.

    Returns
    - courseware_summary is a summary of all sections with problems in the course.
    It is organized as an array of chapters, each containing an array of sections,
    each containing an array of scores. This contains information for graded and
    ungraded problems, and is good for displaying a course summary with due dates,
    etc.
    - None if the student does not have access to load the course module.

    Arguments:
        student: A User object for the student to grade
        course: A Descriptor containing the course to grade

    """
    if course_structure is None:
        course_structure = get_course_blocks(student, course.location)
    if not len(course_structure):
        return ProgressSummary()
    scorable_locations = [block_key for block_key in course_structure if possibly_scored(block_key)]

    with outer_atomic():
        scores_client = ScoresClient.create_for_locations(course.id, student.id, scorable_locations)

    # We need to import this here to avoid a circular dependency of the form:
    # XBlock --> submissions --> Django Rest Framework error strings -->
    # Django translation --> ... --> courseware --> submissions
    from submissions import api as sub_api  # installed from the edx-submissions repository
    with outer_atomic():
        submissions_scores = sub_api.get_scores(
            unicode(course.id), anonymous_id_for_user(student, course.id)
        )

    # Check for gated content
    gated_content = gating_api.get_gated_content(course, student)

    chapters = []
    locations_to_weighted_scores = {}

    for chapter_key in course_structure.get_children(course_structure.root_block_usage_key):
        chapter = course_structure[chapter_key]
        sections = []
        for section_key in course_structure.get_children(chapter_key):
            if unicode(section_key) in gated_content:
                continue

            section = course_structure[section_key]

            graded = getattr(section, 'graded', False)
            scores = []

            for descendant_key in course_structure.post_order_traversal(
                    filter_func=possibly_scored,
                    start_node=section_key,
            ):
                descendant = course_structure[descendant_key]

                (correct, total) = get_score(
                    student,
                    descendant,
                    scores_client,
                    submissions_scores,
                )
                if correct is None and total is None:
                    continue

                weighted_location_score = Score(
                    correct,
                    total,
                    graded,
                    block_metadata_utils.display_name_with_default_escaped(descendant),
                    descendant.location
                )

                scores.append(weighted_location_score)
                locations_to_weighted_scores[descendant.location] = weighted_location_score

            escaped_section_name = block_metadata_utils.display_name_with_default_escaped(section)
            section_total, _ = graders.aggregate_scores(scores, escaped_section_name)

            sections.append({
                'display_name': escaped_section_name,
                'url_name': block_metadata_utils.url_name_for_block(section),
                'scores': scores,
                'section_total': section_total,
                'format': getattr(section, 'format', ''),
                'due': getattr(section, 'due', None),
                'graded': graded,
            })

        chapters.append({
            'course': course.display_name_with_default_escaped,
            'display_name': block_metadata_utils.display_name_with_default_escaped(chapter),
            'url_name': block_metadata_utils.url_name_for_block(chapter),
            'sections': sections
        })

    return ProgressSummary(chapters, locations_to_weighted_scores, course_structure.get_children)
