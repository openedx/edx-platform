# Compute grades using real division, with no integer truncation
from __future__ import division

import json
import logging
import random
from collections import defaultdict

import dogstats_wrapper as dog_stats_api
from course_blocks.api import get_course_blocks
from courseware import courses
from django.conf import settings
from django.core.cache import cache
from django.test.client import RequestFactory
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locator import BlockUsageLocator
from openedx.core.djangoapps.content.block_structure.api import get_course_in_cache
from openedx.core.lib.cache_utils import memoized
from openedx.core.lib.gating import api as gating_api
from courseware.model_data import FieldDataCache, ScoresClient
from openedx.core.djangoapps.signals.signals import GRADES_UPDATED
from student.models import anonymous_id_for_user
from util.db import outer_atomic
from util.module_utils import yield_dynamic_descriptor_descendants
from xblock.core import XBlock
from xmodule import graders, block_metadata_utils
from xmodule.graders import Score
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError
from .models import StudentModule
from .module_render import get_module_for_descriptor
from .transformers.grades import GradesTransformer


log = logging.getLogger("edx.courseware")


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
    def __init__(self, chapters, weighted_scores, locations_to_children):
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


@memoized
def block_types_with_scores():
    """
    Returns the block types that could have a score.

    Something might be a scored item if it is capable of storing a score
    (has_score=True). We also have to include anything that can have children,
    since those children might have scores. We can avoid things like Videos,
    which have state but cannot ever impact someone's grade.
    """
    return frozenset(
        cat for (cat, xblock_class) in XBlock.load_classes() if (
            getattr(xblock_class, 'has_score', False) or getattr(xblock_class, 'has_children', False)
        )
    )


def possibly_scored(usage_key):
    """
    Returns whether the given block could impact grading (i.e. scored, or has children).
    """
    return usage_key.block_type in block_types_with_scores()


def grading_context_for_course(course):
    """
    Same as grading_context, but takes in a course object.
    """
    course_structure = get_course_in_cache(course.id)
    return grading_context(course_structure)


def grading_context(course_structure):
    """
    This returns a dictionary with keys necessary for quickly grading
    a student. They are used by grades.grade()

    The grading context has two keys:
    graded_sections - This contains the sections that are graded, as
        well as all possible children modules that can affect the
        grading. This allows some sections to be skipped if the student
        hasn't seen any part of it.

        The format is a dictionary keyed by section-type. The values are
        arrays of dictionaries containing
            "section_block" : The section block
            "scored_descendant_keys" : An array of usage keys for blocks
                could possibly be in the section, for any student

    all_graded_blocks - This contains a list of all blocks that can
        affect grading a student. This is used to efficiently fetch
        all the xmodule state for a FieldDataCache without walking
        the descriptor tree again.

    """
    all_graded_blocks = []
    all_graded_sections = defaultdict(list)

    for chapter_key in course_structure.get_children(course_structure.root_block_usage_key):
        for section_key in course_structure.get_children(chapter_key):
            section = course_structure[section_key]
            scored_descendants_of_section = [section]
            if section.graded:
                for descendant_key in course_structure.post_order_traversal(
                        filter_func=possibly_scored,
                        start_node=section_key,
                ):
                    scored_descendants_of_section.append(
                        course_structure[descendant_key],
                    )

                # include only those blocks that have scores, not if they are just a parent
                section_info = {
                    'section_block': section,
                    'scored_descendants': [
                        child for child in scored_descendants_of_section
                        if getattr(child, 'has_score', None)
                    ]
                }
                section_format = getattr(section, 'format', '')
                all_graded_sections[section_format].append(section_info)
                all_graded_blocks.extend(scored_descendants_of_section)

    return {
        'all_graded_sections': all_graded_sections,
        'all_graded_blocks': all_graded_blocks,
    }


def answer_distributions(course_key):
    """
    Given a course_key, return answer distributions in the form of a dictionary
    mapping:

      (problem url_name, problem display_name, problem_id) -> {dict: answer -> count}

    Answer distributions are found by iterating through all StudentModule
    entries for a given course with type="problem" and a grade that is not null.
    This means that we only count LoncapaProblems that people have submitted.
    Other types of items like ORA or sequences will not be collected. Empty
    Loncapa problem state that gets created from running the progress page is
    also not counted.

    This method accesses the StudentModule table directly instead of using the
    CapaModule abstraction. The main reason for this is so that we can generate
    the report without any side-effects -- we don't have to worry about answer
    distribution potentially causing re-evaluation of the student answer. This
    also allows us to use the read-replica database, which reduces risk of bad
    locking behavior. And quite frankly, it makes this a lot less confusing.

    Also, we're pulling all available records from the database for this course
    rather than crawling through a student's course-tree -- the latter could
    potentially cause us trouble with A/B testing. The distribution report may
    not be aware of problems that are not visible to the user being used to
    generate the report.

    This method will try to use a read-replica database if one is available.
    """
    # dict: { module.module_state_key : (url_name, display_name) }
    state_keys_to_problem_info = {}  # For caching, used by url_and_display_name

    def url_and_display_name(usage_key):
        """
        For a given usage_key, return the problem's url and display_name.
        Handle modulestore access and caching. This method ignores permissions.

        Raises:
            InvalidKeyError: if the usage_key does not parse
            ItemNotFoundError: if there is no content that corresponds
                to this usage_key.
        """
        problem_store = modulestore()
        if usage_key not in state_keys_to_problem_info:
            problem = problem_store.get_item(usage_key)
            problem_info = (problem.url_name, problem.display_name_with_default_escaped)
            state_keys_to_problem_info[usage_key] = problem_info

        return state_keys_to_problem_info[usage_key]

    # Iterate through all problems submitted for this course in no particular
    # order, and build up our answer_counts dict that we will eventually return
    answer_counts = defaultdict(lambda: defaultdict(int))
    for module in StudentModule.all_submitted_problems_read_only(course_key):
        try:
            state_dict = json.loads(module.state) if module.state else {}
            raw_answers = state_dict.get("student_answers", {})
        except ValueError:
            log.error(
                u"Answer Distribution: Could not parse module state for StudentModule id=%s, course=%s",
                module.id,
                course_key,
            )
            continue

        try:
            url, display_name = url_and_display_name(module.module_state_key.map_into_course(course_key))
            # Each problem part has an ID that is derived from the
            # module.module_state_key (with some suffix appended)
            for problem_part_id, raw_answer in raw_answers.items():
                # Convert whatever raw answers we have (numbers, unicode, None, etc.)
                # to be unicode values. Note that if we get a string, it's always
                # unicode and not str -- state comes from the json decoder, and that
                # always returns unicode for strings.
                answer = unicode(raw_answer)
                answer_counts[(url, display_name, problem_part_id)][answer] += 1

        except (ItemNotFoundError, InvalidKeyError):
            msg = (
                "Answer Distribution: Item {} referenced in StudentModule {} " +
                "for user {} in course {} not found; " +
                "This can happen if a student answered a question that " +
                "was later deleted from the course. This answer will be " +
                "omitted from the answer distribution CSV."
            ).format(
                module.module_state_key, module.id, module.student_id, course_key
            )
            log.warning(msg)
            continue

    return answer_counts


def grade(student, course, keep_raw_scores=False, course_structure=None):
    """
    Returns the grade of the student.

    Also sends a signal to update the minimum grade requirement status.
    """
    grade_summary = _grade(student, course, keep_raw_scores, course_structure)
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


def _grade(student, course, keep_raw_scores, course_structure=None):
    """
    Unwrapped version of "grade"

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

        letter_grade = grade_for_percentage(course.grade_cutoffs, grade_summary['percent'])
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
    Returns the totaled scores, which can be passed to the grader.
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


def grade_for_percentage(grade_cutoffs, percentage):
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


def progress_summary(student, course, course_structure=None):
    """
    Returns progress summary for all chapters in the course.
    """

    progress = _progress_summary(student, course, course_structure)
    if progress:
        return progress.chapters
    else:
        return None


def get_weighted_scores(student, course):
    """
    Uses the _progress_summary method to return a ProgressSummary object
    containing details of a students weighted scores for the course.
    """
    return _progress_summary(student, course)


def _progress_summary(student, course, course_structure=None):
    """
    Unwrapped version of "progress_summary".

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
        return None
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


def weighted_score(raw_correct, raw_total, weight):
    """Return a tuple that represents the weighted (correct, total) score."""
    # If there is no weighting, or weighting can't be applied, return input.
    if weight is None or raw_total == 0:
        return (raw_correct, raw_total)
    return (float(raw_correct) * weight / raw_total, float(weight))


def get_score(user, block, scores_client, submissions_scores_cache):
    """
    Return the score for a user on a problem, as a tuple (correct, total).
    e.g. (5,7) if you got 5 out of 7 points.

    If this problem doesn't have a score, or we couldn't load it, returns (None,
    None).

    user: a Student object
    block: a BlockStructure's BlockData object
    scores_client: an initialized ScoresClient
    submissions_scores_cache: A dict of location names to (earned, possible) point tuples.
           If an entry is found in this cache, it takes precedence.
    """
    submissions_scores_cache = submissions_scores_cache or {}

    if not user.is_authenticated():
        return (None, None)

    location_url = unicode(block.location)
    if location_url in submissions_scores_cache:
        return submissions_scores_cache[location_url]

    if not getattr(block, 'has_score', False):
        # These are not problems, and do not have a score
        return (None, None)

    # Check the score that comes from the ScoresClient (out of CSM).
    # If an entry exists and has a total associated with it, we trust that
    # value. This is important for cases where a student might have seen an
    # older version of the problem -- they're still graded on what was possible
    # when they tried the problem, not what it's worth now.
    score = scores_client.get(block.location)
    if score and score.total is not None:
        # We have a valid score, just use it.
        correct = score.correct if score.correct is not None else 0.0
        total = score.total
    else:
        # This means we don't have a valid score entry and we don't have a
        # cached_max_score on hand. We know they've earned 0.0 points on this.
        correct = 0.0
        total = block.transformer_data[GradesTransformer].max_score

        # Problem may be an error module (if something in the problem builder failed)
        # In which case total might be None
        if total is None:
            return (None, None)

    return weighted_score(correct, total, block.weight)


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
        course = courses.get_course_by_id(course_or_id)
    else:
        course = course_or_id

    for student in students:
        with dog_stats_api.timer('lms.grades.iterate_grades_for', tags=[u'action:{}'.format(course.id)]):
            try:
                gradeset = grade(student, course, keep_raw_scores)
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


def _get_mock_request(student):
    """
    Make a fake request because grading code expects to be able to look at
    the request. We have to attach the correct user to the request before
    grading that student.
    """
    request = RequestFactory().get('/')
    request.user = student
    return request


def _calculate_score_for_modules(user_id, course, modules):
    """
    Calculates the cumulative score (percent) of the given modules
    """

    # removing branch and version from exam modules locator
    # otherwise student module would not return scores since module usage keys would not match
    modules = [m for m in modules]
    locations = [
        BlockUsageLocator(
            course_key=course.id,
            block_type=module.location.block_type,
            block_id=module.location.block_id
        )
        if isinstance(module.location, BlockUsageLocator) and module.location.version
        else module.location
        for module in modules
    ]

    scores_client = ScoresClient(course.id, user_id)
    scores_client.fetch_scores(locations)

    # Iterate over all of the exam modules to get score percentage of user for each of them
    module_percentages = []
    ignore_categories = ['course', 'chapter', 'sequential', 'vertical', 'randomize', 'library_content']
    for index, module in enumerate(modules):
        if module.category not in ignore_categories and (module.graded or module.has_score):
            module_score = scores_client.get(locations[index])
            if module_score:
                correct = module_score.correct or 0
                total = module_score.total or 1
                module_percentages.append(correct / total)

    return sum(module_percentages) / float(len(module_percentages)) if module_percentages else 0


def get_module_score(user, course, module):
    """
    Collects all children of the given module and calculates the cumulative
    score for this set of modules for the given user.

    Arguments:
        user (User): The user
        course (CourseModule): The course
        module (XBlock): The module

    Returns:
        float: The cumulative score
    """
    def inner_get_module(descriptor):
        """
        Delegate to get_module_for_descriptor
        """
        field_data_cache = FieldDataCache([descriptor], course.id, user)
        return get_module_for_descriptor(
            user,
            _get_mock_request(user),
            descriptor,
            field_data_cache,
            course.id,
            course=course
        )

    modules = yield_dynamic_descriptor_descendants(
        module,
        user.id,
        inner_get_module
    )
    return _calculate_score_for_modules(user.id, course, modules)
