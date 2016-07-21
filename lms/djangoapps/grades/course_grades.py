"""
Functionality for course-level grades.
"""
from logging import getLogger
from django.conf import settings
import dogstats_wrapper as dog_stats_api
import random

from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.signals.signals import GRADES_UPDATED

from course_blocks.api import get_course_blocks
from courseware.courses import get_course_by_id
from courseware.model_data import ScoresClient
from student.models import anonymous_id_for_user
from util.db import outer_atomic
from xmodule import graders, block_metadata_utils
from xmodule.graders import Score

from .context import grading_context
from .scores import get_score


log = getLogger(__name__)


def iterate_grades_for(course_or_id, students, keep_raw_scores=False):
    """Given a course_id and an iterable of students (User), yield a tuple of:

    (student, gradeset, err_msg) for every student enrolled in the course.

    If an error occurred, gradeset will be an empty dict and err_msg will be an
    exception message. If there was no error, err_msg is an empty string.

    The gradeset is a dictionary with the following fields:

    - grade : A final letter grade.
    - percent : The final percent for the class (rounded up).
        - section_breakdown : A breakdown of each section that makes
        up the grade. (For display)
    - grade_breakdown : A breakdown of the major components that
        make up the final grade. (For display)
    - raw_scores: contains scores for every graded module
    """
    if isinstance(course_or_id, (basestring, CourseKey)):
        course = get_course_by_id(course_or_id)
    else:
        course = course_or_id

    for student in students:
        with dog_stats_api.timer('lms.grades.iterate_grades_for', tags=[u'action:{}'.format(course.id)]):
            try:
                gradeset = summary(student, course, keep_raw_scores)
                yield student, gradeset, ""
            except Exception as exc:  # pylint: disable=broad-except
                # Keep marching on even if this student couldn't be graded for
                # some reason, but log it for future reference.
                log.exception(
                    'Cannot grade student %s (%s) in course %s because of exception: %s',
                    student.username,
                    student.id,
                    course.id,
                    exc.message
                )
                yield student, {}, exc.message


def summary(student, course, keep_raw_scores=False, course_structure=None):
    """
    Returns the grade summary of the student for the given course.

    Also sends a signal to update the minimum grade requirement status.
    """
    grade_summary = _summary(student, course, keep_raw_scores, course_structure)
    responses = GRADES_UPDATED.send_robust(
        sender=None,
        username=student.username,
        grade_summary=grade_summary,
        course_key=course.id,
        deadline=course.end
    )

    for receiver, response in responses:
        log.info('Signal fired when student grade is calculated. Receiver: %s. Response: %s', receiver, response)

    return grade_summary


def _summary(student, course, keep_raw_scores, course_structure=None):
    """
    This grades a student as quickly as possible. It returns the
    output from the course grader, augmented with the final letter
    grade. The keys in the output are:

    - course: a CourseDescriptor
    - keep_raw_scores : if True, then value for key 'raw_scores' contains scores
      for every graded module

    More information on the format is in the docstring for CourseGrader.
    """
    if course_structure is None:
        course_structure = get_course_blocks(student, course.location)
    grading_context_result = grading_context(course_structure)
    scorable_locations = [block.location for block in grading_context_result['all_graded_blocks']]

    with outer_atomic():
        scores_client = ScoresClient.create_for_locations(course.id, student.id, scorable_locations)

    # Dict of item_ids -> (earned, possible) point tuples. This *only* grabs
    # scores that were registered with the submissions API, which for the moment
    # means only openassessment (edx-ora2)
    # We need to import this here to avoid a circular dependency of the form:
    # XBlock --> submissions --> Django Rest Framework error strings -->
    # Django translation --> ... --> courseware --> submissions
    from submissions import api as sub_api  # installed from the edx-submissions repository

    with outer_atomic():
        submissions_scores = sub_api.get_scores(
            course.id.to_deprecated_string(),
            anonymous_id_for_user(student, course.id)
        )

    totaled_scores, raw_scores = _calculate_totaled_scores(
        student, grading_context_result, submissions_scores, scores_client, keep_raw_scores
    )

    with outer_atomic():
        # Grading policy might be overriden by a CCX, need to reset it
        course.set_grading_policy(course.grading_policy)
        grade_summary = course.grader.grade(totaled_scores, generate_random_scores=settings.GENERATE_PROFILE_SCORES)

        # We round the grade here, to make sure that the grade is a whole percentage and
        # doesn't get displayed differently than it gets grades
        grade_summary['percent'] = round(grade_summary['percent'] * 100 + 0.05) / 100

        letter_grade = _letter_grade(course.grade_cutoffs, grade_summary['percent'])
        grade_summary['grade'] = letter_grade
        grade_summary['totaled_scores'] = totaled_scores   # make this available, eg for instructor download & debugging
        if keep_raw_scores:
            # way to get all RAW scores out to instructor
            # so grader can be double-checked
            grade_summary['raw_scores'] = raw_scores

    return grade_summary


def _calculate_totaled_scores(
        student,
        grading_context_result,
        submissions_scores,
        scores_client,
        keep_raw_scores,
):
    """
    Returns a tuple of totaled scores and raw scores, which can be passed to the grader.
    """
    raw_scores = []
    totaled_scores = {}
    for section_format, sections in grading_context_result['all_graded_sections'].iteritems():
        format_scores = []
        for section_info in sections:
            section = section_info['section_block']
            section_name = block_metadata_utils.display_name_with_default(section)

            with outer_atomic():
                # Check to
                # see if any of our locations are in the scores from the submissions
                # API. If scores exist, we have to calculate grades for this section.
                should_grade_section = any(
                    unicode(descendant.location) in submissions_scores
                    for descendant in section_info['scored_descendants']
                )

                if not should_grade_section:
                    should_grade_section = any(
                        descendant.location in scores_client
                        for descendant in section_info['scored_descendants']
                    )

                # If we haven't seen a single problem in the section, we don't have
                # to grade it at all! We can assume 0%
                if should_grade_section:
                    scores = []

                    for descendant in section_info['scored_descendants']:

                        (correct, total) = get_score(
                            student,
                            descendant,
                            scores_client,
                            submissions_scores,
                        )
                        if correct is None and total is None:
                            continue

                        if settings.GENERATE_PROFILE_SCORES:  # for debugging!
                            if total > 1:
                                correct = random.randrange(max(total - 2, 1), total + 1)
                            else:
                                correct = total

                        graded = descendant.graded
                        if not total > 0:
                            # We simply cannot grade a problem that is 12/0, because we might need it as a percentage
                            graded = False

                        scores.append(
                            Score(
                                correct,
                                total,
                                graded,
                                block_metadata_utils.display_name_with_default_escaped(descendant),
                                descendant.location
                            )
                        )

                    __, graded_total = graders.aggregate_scores(scores, section_name)
                    if keep_raw_scores:
                        raw_scores += scores
                else:
                    graded_total = Score(0.0, 1.0, True, section_name, None)

                # Add the graded total to totaled_scores
                if graded_total.possible > 0:
                    format_scores.append(graded_total)
                else:
                    log.info(
                        "Unable to grade a section with a total possible score of zero. " +
                        str(section.location)
                    )

        totaled_scores[section_format] = format_scores

    return totaled_scores, raw_scores


def _letter_grade(grade_cutoffs, percentage):
    """
    Returns a letter grade as defined in grading_policy (e.g. 'A' 'B' 'C' for 6.002x) or None.

    Arguments
    - grade_cutoffs is a dictionary mapping a grade to the lowest
        possible percentage to earn that grade.
    - percentage is the final percent across all problems in a course
    """

    letter_grade = None

    # Possible grades, sorted in descending order of score
    descending_grades = sorted(grade_cutoffs, key=lambda x: grade_cutoffs[x], reverse=True)
    for possible_grade in descending_grades:
        if percentage >= grade_cutoffs[possible_grade]:
            letter_grade = possible_grade
            break

    return letter_grade
