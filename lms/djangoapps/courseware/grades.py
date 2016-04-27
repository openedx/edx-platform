# Compute grades using real division, with no integer truncation
from __future__ import division
from collections import defaultdict
from functools import partial
import json
import random
import logging

from contextlib import contextmanager
from django.conf import settings
from django.db import transaction
from django.test.client import RequestFactory
from django.core.cache import cache

import dogstats_wrapper as dog_stats_api

from courseware import courses
from courseware.access import has_access
from courseware.model_data import FieldDataCache, ScoresClient
from student.models import anonymous_id_for_user
from util.module_utils import yield_dynamic_descriptor_descendants
from xmodule import graders
from xmodule.graders import Score
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError
from .models import StudentModule
from .module_render import get_module_for_descriptor
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.signals.signals import GRADES_UPDATED


log = logging.getLogger("edx.courseware")


class MaxScoresCache(object):
    """
    A cache for unweighted max scores for problems.

    The key assumption here is that any problem that has not yet recorded a
    score for a user is worth the same number of points. An XBlock is free to
    score one student at 2/5 and another at 1/3. But a problem that has never
    issued a score -- say a problem two students have only seen mentioned in
    their progress pages and never interacted with -- should be worth the same
    number of points for everyone.
    """
    def __init__(self, cache_prefix):
        self.cache_prefix = cache_prefix
        self._max_scores_cache = {}
        self._max_scores_updates = {}

    @classmethod
    def create_for_course(cls, course):
        """
        Given a CourseDescriptor, return a correctly configured `MaxScoresCache`

        This method will base the `MaxScoresCache` cache prefix value on the
        last time something was published to the live version of the course.
        This is so that we don't have to worry about stale cached values for
        max scores -- any time a content change occurs, we change our cache
        keys.
        """
        if course.subtree_edited_on is None:
            # check for subtree_edited_on because old XML courses doesn't have this attribute
            cache_key = u"{}".format(course.id)
        else:
            cache_key = u"{}.{}".format(course.id, course.subtree_edited_on.isoformat())
        return cls(cache_key)

    def fetch_from_remote(self, locations):
        """
        Populate the local cache with values from django's cache
        """
        remote_dict = cache.get_many([self._remote_cache_key(loc) for loc in locations])
        self._max_scores_cache = {
            self._local_cache_key(remote_key): value
            for remote_key, value in remote_dict.items()
            if value is not None
        }

    def push_to_remote(self):
        """
        Update the remote cache
        """
        if self._max_scores_updates:
            cache.set_many(
                {
                    self._remote_cache_key(key): value
                    for key, value in self._max_scores_updates.items()
                },
                60 * 60 * 24  # 1 day
            )

    def _remote_cache_key(self, location):
        """Convert a location to a remote cache key (add our prefixing)."""
        return u"grades.MaxScores.{}___{}".format(self.cache_prefix, unicode(location))

    def _local_cache_key(self, remote_key):
        """Convert a remote cache key to a local cache key (i.e. location str)."""
        return remote_key.split(u"___", 1)[1]

    def num_cached_from_remote(self):
        """How many items did we pull down from the remote cache?"""
        return len(self._max_scores_cache)

    def num_cached_updates(self):
        """How many local updates are we waiting to push to the remote cache?"""
        return len(self._max_scores_updates)

    def set(self, location, max_score):
        """
        Adds a max score to the max_score_cache
        """
        loc_str = unicode(location)
        if self._max_scores_cache.get(loc_str) != max_score:
            self._max_scores_updates[loc_str] = max_score

    def get(self, location):
        """
        Retrieve a max score from the cache
        """
        loc_str = unicode(location)
        max_score = self._max_scores_updates.get(loc_str)
        if max_score is None:
            max_score = self._max_scores_cache.get(loc_str)

        return max_score


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

       locations_to_children: a dictionary mapping module locations to their
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


def descriptor_affects_grading(block_types_affecting_grading, descriptor):
    """
    Returns True if the descriptor could have any impact on grading, else False.

    Something might be a scored item if it is capable of storing a score
    (has_score=True). We also have to include anything that can have children,
    since those children might have scores. We can avoid things like Videos,
    which have state but cannot ever impact someone's grade.
    """
    return descriptor.location.block_type in block_types_affecting_grading


def field_data_cache_for_grading(course, user):
    """
    Given a CourseDescriptor and User, create the FieldDataCache for grading.

    This will generate a FieldDataCache that only loads state for those things
    that might possibly affect the grading process, and will ignore things like
    Videos.
    """
    descriptor_filter = partial(descriptor_affects_grading, course.block_types_affecting_grading)
    return FieldDataCache.cache_for_descriptor_descendents(
        course.id,
        user,
        course,
        depth=None,
        descriptor_filter=descriptor_filter
    )


def answer_distributions(course_key):
    """
    Given a course_key, return answer distributions in the form of a dictionary
    mapping:

      (problem url_name, problem display_name, problem_id) -> {dict: answer -> count}

    Answer distributions are found by iterating through all StudentModule
    entries for a given course with type="problem" and a grade that is not null.
    This means that we only count LoncapaProblems that people have submitted.
    Other types of items like ORA or sequences will not be collected. Empty
    Loncapa problem state that gets created from runnig the progress page is
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
            problem_info = (problem.url_name, problem.display_name_with_default)
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


@transaction.commit_manually
def grade(student, request, course, keep_raw_scores=False, field_data_cache=None, scores_client=None):
    """
    Wraps "_grade" with the manual_transaction context manager just in case
    there are unanticipated errors.
    Send a signal to update the minimum grade requirement status.
    """
    with manual_transaction():
        grade_summary = _grade(student, request, course, keep_raw_scores, field_data_cache, scores_client)
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


def _grade(student, request, course, keep_raw_scores, field_data_cache, scores_client):
    """
    Unwrapped version of "grade"

    This grades a student as quickly as possible. It returns the
    output from the course grader, augmented with the final letter
    grade. The keys in the output are:

    course: a CourseDescriptor

    - grade : A final letter grade.
    - percent : The final percent for the class (rounded up).
    - section_breakdown : A breakdown of each section that makes
      up the grade. (For display)
    - grade_breakdown : A breakdown of the major components that
      make up the final grade. (For display)
    - keep_raw_scores : if True, then value for key 'raw_scores' contains scores
      for every graded module

    More information on the format is in the docstring for CourseGrader.
    """
    if field_data_cache is None:
        with manual_transaction():
            field_data_cache = field_data_cache_for_grading(course, student)
    if scores_client is None:
        scores_client = ScoresClient.from_field_data_cache(field_data_cache)

    # Dict of item_ids -> (earned, possible) point tuples. This *only* grabs
    # scores that were registered with the submissions API, which for the moment
    # means only openassessment (edx-ora2)
    # We need to import this here to avoid a circular dependency of the form:
    # XBlock --> submissions --> Django Rest Framework error strings -->
    # Django translation --> ... --> courseware --> submissions
    from submissions import api as sub_api  # installed from the edx-submissions repository
    submissions_scores = sub_api.get_scores(course.id.to_deprecated_string(), anonymous_id_for_user(student, course.id))
    max_scores_cache = MaxScoresCache.create_for_course(course)

    # For the moment, we have to get scorable_locations from field_data_cache
    # and not from scores_client, because scores_client is ignorant of things
    # in the submissions API. As a further refactoring step, submissions should
    # be hidden behind the ScoresClient.
    max_scores_cache.fetch_from_remote(field_data_cache.scorable_locations)

    grading_context = course.grading_context
    raw_scores = []

    totaled_scores = {}
    # This next complicated loop is just to collect the totaled_scores, which is
    # passed to the grader
    for section_format, sections in grading_context['graded_sections'].iteritems():
        format_scores = []
        for section in sections:
            section_descriptor = section['section_descriptor']
            section_name = section_descriptor.display_name_with_default

            # some problems have state that is updated independently of interaction
            # with the LMS, so they need to always be scored. (E.g. foldit.,
            # combinedopenended)
            should_grade_section = any(
                descriptor.always_recalculate_grades for descriptor in section['xmoduledescriptors']
            )

            # If there are no problems that always have to be regraded, check to
            # see if any of our locations are in the scores from the submissions
            # API. If scores exist, we have to calculate grades for this section.
            if not should_grade_section:
                should_grade_section = any(
                    descriptor.location.to_deprecated_string() in submissions_scores
                    for descriptor in section['xmoduledescriptors']
                )

            if not should_grade_section:
                should_grade_section = any(
                    descriptor.location in scores_client
                    for descriptor in section['xmoduledescriptors']
                )

            # If we haven't seen a single problem in the section, we don't have
            # to grade it at all! We can assume 0%
            if should_grade_section:
                scores = []

                def create_module(descriptor):
                    '''creates an XModule instance given a descriptor'''
                    # TODO: We need the request to pass into here. If we could forego that, our arguments
                    # would be simpler
                    return get_module_for_descriptor(
                        student, request, descriptor, field_data_cache, course.id, course=course
                    )

                descendants = yield_dynamic_descriptor_descendants(section_descriptor, student.id, create_module)
                for module_descriptor in descendants:
                    user_access = has_access(student, 'load', module_descriptor, module_descriptor.location.course_key)
                    if not user_access:
                        continue

                    (correct, total) = get_score(
                        student,
                        module_descriptor,
                        create_module,
                        scores_client,
                        submissions_scores,
                        max_scores_cache,
                    )
                    if correct is None and total is None:
                        continue

                    if settings.GENERATE_PROFILE_SCORES:    # for debugging!
                        if total > 1:
                            correct = random.randrange(max(total - 2, 1), total + 1)
                        else:
                            correct = total

                    graded = module_descriptor.graded
                    if not total > 0:
                        # We simply cannot grade a problem that is 12/0, because we might need it as a percentage
                        graded = False

                    scores.append(
                        Score(
                            correct,
                            total,
                            graded,
                            module_descriptor.display_name_with_default,
                            module_descriptor.location
                        )
                    )

                __, graded_total = graders.aggregate_scores(scores, section_name)
                if keep_raw_scores:
                    raw_scores += scores
            else:
                graded_total = Score(0.0, 1.0, True, section_name, None)

            #Add the graded total to totaled_scores
            if graded_total.possible > 0:
                format_scores.append(graded_total)
            else:
                log.info(
                    "Unable to grade a section with a total possible score of zero. " +
                    str(section_descriptor.location)
                )

        totaled_scores[section_format] = format_scores

    # Grading policy might be overriden by a CCX, need to reset it
    course.set_grading_policy(course.grading_policy)
    grade_summary = course.grader.grade(totaled_scores, generate_random_scores=settings.GENERATE_PROFILE_SCORES)

    # We round the grade here, to make sure that the grade is an whole percentage and
    # doesn't get displayed differently than it gets grades
    grade_summary['percent'] = round(grade_summary['percent'] * 100 + 0.05) / 100

    letter_grade = grade_for_percentage(course.grade_cutoffs, grade_summary['percent'])
    grade_summary['grade'] = letter_grade
    grade_summary['totaled_scores'] = totaled_scores   # make this available, eg for instructor download & debugging
    if keep_raw_scores:
        # way to get all RAW scores out to instructor
        # so grader can be double-checked
        grade_summary['raw_scores'] = raw_scores

    max_scores_cache.push_to_remote()

    return grade_summary


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


@transaction.commit_manually
def progress_summary(student, request, course, field_data_cache=None, scores_client=None):
    """
    Wraps "_progress_summary" with the manual_transaction context manager just
    in case there are unanticipated errors.
    """
    with manual_transaction():
        progress = _progress_summary(student, request, course, field_data_cache, scores_client)
        if progress:
            return progress.chapters
        else:
            return None


@transaction.commit_manually
def get_weighted_scores(student, course, field_data_cache=None, scores_client=None):
    """
    Uses the _progress_summary method to return a ProgressSummmary object
    containing details of a students weighted scores for the course.
    """
    with manual_transaction():
        request = _get_mock_request(student)
        return _progress_summary(student, request, course, field_data_cache, scores_client)


# TODO: This method is not very good. It was written in the old course style and
# then converted over and performance is not good. Once the progress page is redesigned
# to not have the progress summary this method should be deleted (so it won't be copied).
def _progress_summary(student, request, course, field_data_cache=None, scores_client=None):
    """
    Unwrapped version of "progress_summary".

    This pulls a summary of all problems in the course.

    Returns
    - courseware_summary is a summary of all sections with problems in the course.
    It is organized as an array of chapters, each containing an array of sections,
    each containing an array of scores. This contains information for graded and
    ungraded problems, and is good for displaying a course summary with due dates,
    etc.

    Arguments:
        student: A User object for the student to grade
        course: A Descriptor containing the course to grade

    If the student does not have access to load the course module, this function
    will return None.

    """
    with manual_transaction():
        if field_data_cache is None:
            field_data_cache = field_data_cache_for_grading(course, student)
        if scores_client is None:
            scores_client = ScoresClient.from_field_data_cache(field_data_cache)

        course_module = get_module_for_descriptor(
            student, request, course, field_data_cache, course.id, course=course
        )
        if not course_module:
            return None

        course_module = getattr(course_module, '_x_module', course_module)

    # We need to import this here to avoid a circular dependency of the form:
    # XBlock --> submissions --> Django Rest Framework error strings -->
    # Django translation --> ... --> courseware --> submissions
    from submissions import api as sub_api  # installed from the edx-submissions repository
    submissions_scores = sub_api.get_scores(course.id.to_deprecated_string(), anonymous_id_for_user(student, course.id))

    max_scores_cache = MaxScoresCache.create_for_course(course)
    # For the moment, we have to get scorable_locations from field_data_cache
    # and not from scores_client, because scores_client is ignorant of things
    # in the submissions API. As a further refactoring step, submissions should
    # be hidden behind the ScoresClient.
    max_scores_cache.fetch_from_remote(field_data_cache.scorable_locations)

    chapters = []
    locations_to_children = defaultdict(list)
    locations_to_weighted_scores = {}
    # Don't include chapters that aren't displayable (e.g. due to error)
    for chapter_module in course_module.get_display_items():
        # Skip if the chapter is hidden
        if chapter_module.hide_from_toc:
            continue

        sections = []
        for section_module in chapter_module.get_display_items():
            # Skip if the section is hidden
            with manual_transaction():
                if section_module.hide_from_toc:
                    continue

                graded = section_module.graded
                scores = []

                module_creator = section_module.xmodule_runtime.get_module

                for module_descriptor in yield_dynamic_descriptor_descendants(
                        section_module, student.id, module_creator
                ):
                    locations_to_children[module_descriptor.parent].append(module_descriptor.location)
                    (correct, total) = get_score(
                        student,
                        module_descriptor,
                        module_creator,
                        scores_client,
                        submissions_scores,
                        max_scores_cache,
                    )
                    if correct is None and total is None:
                        continue

                    weighted_location_score = Score(
                        correct,
                        total,
                        graded,
                        module_descriptor.display_name_with_default,
                        module_descriptor.location
                    )

                    scores.append(weighted_location_score)
                    locations_to_weighted_scores[module_descriptor.location] = weighted_location_score

                scores.reverse()
                section_total, _ = graders.aggregate_scores(
                    scores, section_module.display_name_with_default)

                module_format = section_module.format if section_module.format is not None else ''
                sections.append({
                    'display_name': section_module.display_name_with_default,
                    'url_name': section_module.url_name,
                    'scores': scores,
                    'section_total': section_total,
                    'format': module_format,
                    'due': section_module.due,
                    'graded': graded,
                })

        chapters.append({
            'course': course.display_name_with_default,
            'display_name': chapter_module.display_name_with_default,
            'url_name': chapter_module.url_name,
            'sections': sections
        })

    max_scores_cache.push_to_remote()

    return ProgressSummary(chapters, locations_to_weighted_scores, locations_to_children)


def weighted_score(raw_correct, raw_total, weight):
    """Return a tuple that represents the weighted (correct, total) score."""
    # If there is no weighting, or weighting can't be applied, return input.
    if weight is None or raw_total == 0:
        return (raw_correct, raw_total)
    return (float(raw_correct) * weight / raw_total, float(weight))


def get_score(user, problem_descriptor, module_creator, scores_client, submissions_scores_cache, max_scores_cache):
    """
    Return the score for a user on a problem, as a tuple (correct, total).
    e.g. (5,7) if you got 5 out of 7 points.

    If this problem doesn't have a score, or we couldn't load it, returns (None,
    None).

    user: a Student object
    problem_descriptor: an XModuleDescriptor
    scores_client: an initialized ScoresClient
    module_creator: a function that takes a descriptor, and returns the corresponding XModule for this user.
           Can return None if user doesn't have access, or if something else went wrong.
    submissions_scores_cache: A dict of location names to (earned, possible) point tuples.
           If an entry is found in this cache, it takes precedence.
    max_scores_cache: a MaxScoresCache
    """
    submissions_scores_cache = submissions_scores_cache or {}

    if not user.is_authenticated():
        return (None, None)

    location_url = problem_descriptor.location.to_deprecated_string()
    if location_url in submissions_scores_cache:
        return submissions_scores_cache[location_url]

    # some problems have state that is updated independently of interaction
    # with the LMS, so they need to always be scored. (E.g. foldit.)
    if problem_descriptor.always_recalculate_grades:
        problem = module_creator(problem_descriptor)
        if problem is None:
            return (None, None)
        score = problem.get_score()
        if score is not None:
            return (score['score'], score['total'])
        else:
            return (None, None)

    if not problem_descriptor.has_score:
        # These are not problems, and do not have a score
        return (None, None)

    # Check the score that comes from the ScoresClient (out of CSM).
    # If an entry exists and has a total associated with it, we trust that
    # value. This is important for cases where a student might have seen an
    # older version of the problem -- they're still graded on what was possible
    # when they tried the problem, not what it's worth now.
    score = scores_client.get(problem_descriptor.location)
    cached_max_score = max_scores_cache.get(problem_descriptor.location)
    if score and score.total is not None:
        # We have a valid score, just use it.
        correct = score.correct if score.correct is not None else 0.0
        total = score.total
    elif cached_max_score is not None and settings.FEATURES.get("ENABLE_MAX_SCORE_CACHE"):
        # We don't have a valid score entry but we know from our cache what the
        # max possible score is, so they've earned 0.0 / cached_max_score
        correct = 0.0
        total = cached_max_score
    else:
        # This means we don't have a valid score entry and we don't have a
        # cached_max_score on hand. We know they've earned 0.0 points on this,
        # but we need to instantiate the module (i.e. load student state) in
        # order to find out how much it was worth.
        problem = module_creator(problem_descriptor)
        if problem is None:
            return (None, None)

        correct = 0.0
        total = problem.max_score()

        # Problem may be an error module (if something in the problem builder failed)
        # In which case total might be None
        if total is None:
            return (None, None)
        else:
            # add location to the max score cache
            max_scores_cache.set(problem_descriptor.location, total)

    return weighted_score(correct, total, problem_descriptor.weight)


@contextmanager
def manual_transaction():
    """A context manager for managing manual transactions"""
    try:
        yield
    except Exception:
        transaction.rollback()
        log.exception('Due to an error, this transaction has been rolled back')
        raise
    else:
        transaction.commit()


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
                request = _get_mock_request(student)
                # Grading calls problem rendering, which calls masquerading,
                # which checks session vars -- thus the empty session dict below.
                # It's not pretty, but untangling that is currently beyond the
                # scope of this feature.
                request.session = {}
                gradeset = grade(student, request, course, keep_raw_scores)
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
