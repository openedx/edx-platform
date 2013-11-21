# Compute grades using real division, with no integer truncation
from __future__ import division

import random
import logging

from collections import defaultdict
from django.conf import settings
from django.contrib.auth.models import User

from courseware.model_data import FieldDataCache, DjangoKeyValueStore
from xblock.fields import Scope
from .module_render import get_module, get_module_for_descriptor
from xmodule import graders
from xmodule.capa_module import CapaDescriptor
from xmodule.graders import Score
from .models import StudentModule

log = logging.getLogger("mitx.courseware")


def yield_module_descendents(module):
    stack = module.get_display_items()
    stack.reverse()

    while len(stack) > 0:
        next_module = stack.pop()
        stack.extend(next_module.get_display_items())
        yield next_module


def yield_dynamic_descriptor_descendents(descriptor, module_creator):
    """
    This returns all of the descendants of a descriptor. If the descriptor
    has dynamic children, the module will be created using module_creator
    and the children (as descriptors) of that module will be returned.
    """
    def get_dynamic_descriptor_children(descriptor):
        if descriptor.has_dynamic_children():
            module = module_creator(descriptor)
            if module is None:
                return []
            return module.get_child_descriptors()
        else:
            return descriptor.get_children()

    stack = [descriptor]

    while len(stack) > 0:
        next_descriptor = stack.pop()
        stack.extend(get_dynamic_descriptor_children(next_descriptor))
        yield next_descriptor


def yield_problems(request, course, student):
    """
    Return an iterator over capa_modules that this student has
    potentially answered.  (all that student has answered will definitely be in
    the list, but there may be others as well).
    """
    grading_context = course.grading_context

    descriptor_locations = (descriptor.location.url() for descriptor in grading_context['all_descriptors'])
    existing_student_modules = set(StudentModule.objects.filter(
        module_state_key__in=descriptor_locations
    ).values_list('module_state_key', flat=True))

    sections_to_list = []
    for _, sections in grading_context['graded_sections'].iteritems():
        for section in sections:

            section_descriptor = section['section_descriptor']

            # If the student hasn't seen a single problem in the section, skip it.
            for moduledescriptor in section['xmoduledescriptors']:
                if moduledescriptor.location.url() in existing_student_modules:
                    sections_to_list.append(section_descriptor)
                    break

    field_data_cache = FieldDataCache(sections_to_list, course.id, student)
    for section_descriptor in sections_to_list:
        section_module = get_module(student, request,
                                    section_descriptor.location, field_data_cache,
                                    course.id)
        if section_module is None:
            # student doesn't have access to this module, or something else
            # went wrong.
            # log.debug("couldn't get module for student {0} for section location {1}"
            #           .format(student.username, section_descriptor.location))
            continue

        for problem in yield_module_descendents(section_module):
            problem_desc = get_module(student, request, problem.location, field_data_cache, course.id)
            if isinstance(problem_desc, CapaDescriptor):
                yield problem_desc


def answer_distributions(request, course):
    """
    Given a course_descriptor, compute frequencies of answers for each problem:

    Format is:

    dict: (problem url_name, problem display_name, problem_id) -> (dict : answer ->  count)

    TODO (vshnayder): this is currently doing a full linear pass through all
    students and all problems.  This will be just a little slow.
    """

    counts = defaultdict(lambda: defaultdict(int))

    enrolled_students = User.objects.filter(courseenrollment__course_id=course.id)

    for student in enrolled_students:
        try:
            for capa_desc in yield_problems(request, course, student):
                for problem_id in capa_desc.lcp.student_answers:
                    # Answer can be a list or some other unhashable element.  Convert to string.
                    answer = str(capa_desc.lcp.student_answers[problem_id])
                    key = (capa_desc.url_name, capa_desc.display_name_with_default, problem_id)
                    counts[key][answer] += 1
        except AssertionError as e:
            log.exception(e)
            continue

    return counts


def grade(student, request, course, field_data_cache=None, keep_raw_scores=False):
    """
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
    - keep_raw_scores : if True, then value for key 'raw_scores' contains scores for every graded module

    More information on the format is in the docstring for CourseGrader.
    """

    grading_context = course.grading_context
    raw_scores = []

    if field_data_cache is None:
        field_data_cache = FieldDataCache(grading_context['all_descriptors'], course.id, student)

    totaled_scores = {}
    # This next complicated loop is just to collect the totaled_scores, which is
    # passed to the grader
    for section_format, sections in grading_context['graded_sections'].iteritems():
        format_scores = []
        for section in sections:
            section_descriptor = section['section_descriptor']
            section_name = section_descriptor.display_name_with_default

            should_grade_section = False
            # If we haven't seen a single problem in the section, we don't have to grade it at all! We can assume 0%
            for moduledescriptor in section['xmoduledescriptors']:
                # some problems have state that is updated independently of interaction
                # with the LMS, so they need to always be scored. (E.g. foldit.)
                if moduledescriptor.always_recalculate_grades:
                    should_grade_section = True
                    break

                # Create a fake key to pull out a StudentModule object from the FieldDataCache

                key = DjangoKeyValueStore.Key(
                    Scope.user_state,
                    student.id,
                    moduledescriptor.location,
                    None
                )
                if field_data_cache.find(key):
                    should_grade_section = True
                    break

            if should_grade_section:
                scores = []

                def create_module(descriptor):
                    '''creates an XModule instance given a descriptor'''
                    # TODO: We need the request to pass into here. If we could forego that, our arguments
                    # would be simpler
                    return get_module_for_descriptor(student, request, descriptor, field_data_cache, course.id)

                for module_descriptor in yield_dynamic_descriptor_descendents(section_descriptor, create_module):

                    (correct, total) = get_score(course.id, student, module_descriptor, create_module, field_data_cache)
                    if correct is None and total is None:
                        continue

                    if settings.GENERATE_PROFILE_SCORES:  	# for debugging!
                        if total > 1:
                            correct = random.randrange(max(total - 2, 1), total + 1)
                        else:
                            correct = total

                    graded = module_descriptor.graded
                    if not total > 0:
                        #We simply cannot grade a problem that is 12/0, because we might need it as a percentage
                        graded = False

                    scores.append(Score(correct, total, graded, module_descriptor.display_name_with_default))

                _, graded_total = graders.aggregate_scores(scores, section_name)
                if keep_raw_scores:
                    raw_scores += scores
            else:
                graded_total = Score(0.0, 1.0, True, section_name)

            #Add the graded total to totaled_scores
            if graded_total.possible > 0:
                format_scores.append(graded_total)
            else:
                log.exception("Unable to grade a section with a total possible score of zero. " +
                              str(section_descriptor.location))

        totaled_scores[section_format] = format_scores

    grade_summary = course.grader.grade(totaled_scores, generate_random_scores=settings.GENERATE_PROFILE_SCORES)

    # We round the grade here, to make sure that the grade is an whole percentage and
    # doesn't get displayed differently than it gets grades
    grade_summary['percent'] = round(grade_summary['percent'] * 100 + 0.05) / 100

    letter_grade = grade_for_percentage(course.grade_cutoffs, grade_summary['percent'])
    grade_summary['grade'] = letter_grade
    grade_summary['totaled_scores'] = totaled_scores  	# make this available, eg for instructor download & debugging
    if keep_raw_scores:
        grade_summary['raw_scores'] = raw_scores        # way to get all RAW scores out to instructor
                                                        # so grader can be double-checked
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


# TODO: This method is not very good. It was written in the old course style and
# then converted over and performance is not good. Once the progress page is redesigned
# to not have the progress summary this method should be deleted (so it won't be copied).
def progress_summary(student, request, course, field_data_cache):
    """
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
        field_data_cache: A FieldDataCache initialized with all
             instance_modules for the student

    If the student does not have access to load the course module, this function
    will return None.

    """

    # TODO: We need the request to pass into here. If we could forego that, our arguments
    # would be simpler
    course_module = get_module_for_descriptor(student, request, course, field_data_cache, course.id)
    if not course_module:
        # This student must not have access to the course.
        return None

    chapters = []
    # Don't include chapters that aren't displayable (e.g. due to error)
    for chapter_module in course_module.get_display_items():
        # Skip if the chapter is hidden
        if chapter_module.hide_from_toc:
            continue

        sections = []
        for section_module in chapter_module.get_display_items():
            # Skip if the section is hidden
            if section_module.hide_from_toc:
                continue

            # Same for sections
            graded = section_module.graded
            scores = []

            module_creator = section_module.xmodule_runtime.get_module

            for module_descriptor in yield_dynamic_descriptor_descendents(section_module, module_creator):

                course_id = course.id
                (correct, total) = get_score(course_id, student, module_descriptor, module_creator, field_data_cache)
                if correct is None and total is None:
                    continue

                scores.append(Score(correct, total, graded, module_descriptor.display_name_with_default))

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

        chapters.append({'course': course.display_name_with_default,
                         'display_name': chapter_module.display_name_with_default,
                         'url_name': chapter_module.url_name,
                         'sections': sections})

    return chapters


def get_score(course_id, user, problem_descriptor, module_creator, field_data_cache):
    """
    Return the score for a user on a problem, as a tuple (correct, total).
    e.g. (5,7) if you got 5 out of 7 points.

    If this problem doesn't have a score, or we couldn't load it, returns (None,
    None).

    user: a Student object
    problem_descriptor: an XModuleDescriptor
    module_creator: a function that takes a descriptor, and returns the corresponding XModule for this user.
           Can return None if user doesn't have access, or if something else went wrong.
    cache: A FieldDataCache
    """
    if not user.is_authenticated():
        return (None, None)

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

    # Create a fake KeyValueStore key to pull out the StudentModule
    key = DjangoKeyValueStore.Key(
        Scope.user_state,
        user.id,
        problem_descriptor.location,
        None
    )

    student_module = field_data_cache.find(key)

    if student_module is not None and student_module.max_grade is not None:
        correct = student_module.grade if student_module.grade is not None else 0
        total = student_module.max_grade
    else:
        # If the problem was not in the cache, or hasn't been graded yet,
        # we need to instantiate the problem.
        # Otherwise, the max score (cached in student_module) won't be available
        problem = module_creator(problem_descriptor)
        if problem is None:
            return (None, None)

        correct = 0.0
        total = problem.max_score()

        # Problem may be an error module (if something in the problem builder failed)
        # In which case total might be None
        if total is None:
            return (None, None)

    # Now we re-weight the problem, if specified
    weight = problem_descriptor.weight
    if weight is not None:
        if total == 0:
            log.exception("Cannot reweight a problem with zero total points. Problem: " + str(student_module))
            return (correct, total)
        correct = correct * weight / total
        total = weight

    return (correct, total)
