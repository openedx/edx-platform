# Compute grades using real division, with no integer truncation
from __future__ import division

import random
import logging

from django.conf import settings

from models import StudentModuleCache
from module_render import get_module, get_instance_module
from xmodule import graders
from xmodule.course_module import CourseDescriptor
from xmodule.graders import Score
from models import StudentModule

log = logging.getLogger("mitx.courseware")

def yield_module_descendents(module):
    stack = module.get_display_items()
    stack.reverse()

    while len(stack) > 0:
        next_module = stack.pop()
        stack.extend( next_module.get_display_items() )
        yield next_module

def grade(student, request, course, student_module_cache=None, keep_raw_scores=False):
    """
    This grades a student as quickly as possible. It retuns the
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

    if student_module_cache == None:
        student_module_cache = StudentModuleCache(course.id, student, grading_context['all_descriptors'])

    totaled_scores = {}
    # This next complicated loop is just to collect the totaled_scores, which is
    # passed to the grader
    for section_format, sections in grading_context['graded_sections'].iteritems():
        format_scores = []
        for section in sections:
            section_descriptor = section['section_descriptor']
            section_name = section_descriptor.metadata.get('display_name')

            should_grade_section = False
            # If we haven't seen a single problem in the section, we don't have to grade it at all! We can assume 0%
            for moduledescriptor in section['xmoduledescriptors']:
                if student_module_cache.lookup(
                        course.id, moduledescriptor.category, moduledescriptor.location.url()):
                    should_grade_section = True
                    break

            if should_grade_section:
                scores = []
                # TODO: We need the request to pass into here. If we could forgo that, our arguments
                # would be simpler
                section_module = get_module(student, request,
                                            section_descriptor.location, student_module_cache,
                                            course.id)
                if section_module is None:
                    # student doesn't have access to this module, or something else
                    # went wrong.
                    continue

                # TODO: We may be able to speed this up by only getting a list of children IDs from section_module
                # Then, we may not need to instatiate any problems if they are already in the database
                for module in yield_module_descendents(section_module):
                    (correct, total) = get_score(course.id, student, module, student_module_cache)
                    if correct is None and total is None:
                        continue

                    if settings.GENERATE_PROFILE_SCORES:	# for debugging!
                        if total > 1:
                            correct = random.randrange(max(total - 2, 1), total + 1)
                        else:
                            correct = total

                    graded = module.metadata.get("graded", False)
                    if not total > 0:
                        #We simply cannot grade a problem that is 12/0, because we might need it as a percentage
                        graded = False

                    scores.append(Score(correct, total, graded, module.metadata.get('display_name')))

                section_total, graded_total = graders.aggregate_scores(scores, section_name)
                if keep_raw_scores:
                    raw_scores += scores
            else:
                section_total = Score(0.0, 1.0, False, section_name)
                graded_total = Score(0.0, 1.0, True, section_name)

            #Add the graded total to totaled_scores
            if graded_total.possible > 0:
                format_scores.append(graded_total)
            else:
                log.exception("Unable to grade a section with a total possible score of zero. " + str(section_descriptor.location))

        totaled_scores[section_format] = format_scores

    grade_summary = course.grader.grade(totaled_scores)

    # We round the grade here, to make sure that the grade is an whole percentage and
    # doesn't get displayed differently than it gets grades
    grade_summary['percent'] = round(grade_summary['percent'] * 100 + 0.05) / 100

    letter_grade = grade_for_percentage(course.grade_cutoffs, grade_summary['percent'])
    grade_summary['grade'] = letter_grade
    grade_summary['totaled_scores'] = totaled_scores	# make this available, eg for instructor download & debugging
    if keep_raw_scores:
        grade_summary['raw_scores'] = raw_scores        # way to get all RAW scores out to instructor
                                                        # so grader can be double-checked
    return grade_summary

def grade_for_percentage(grade_cutoffs, percentage):
    """
    Returns a letter grade 'A' 'B' 'C' or None.

    Arguments
    - grade_cutoffs is a dictionary mapping a grade to the lowest
        possible percentage to earn that grade.
    - percentage is the final percent across all problems in a course
    """

    letter_grade = None
    for possible_grade in ['A', 'B', 'C']:
        if percentage >= grade_cutoffs[possible_grade]:
            letter_grade = possible_grade
            break

    return letter_grade

def progress_summary(student, course, grader, student_module_cache):
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
        course: An XModule containing the course to grade
        student_module_cache: A StudentModuleCache initialized with all
             instance_modules for the student
    """
    chapters = []
    # Don't include chapters that aren't displayable (e.g. due to error)
    for c in course.get_display_items():
        # Skip if the chapter is hidden
        hidden = c.metadata.get('hide_from_toc','false')
        if hidden.lower() == 'true':
            continue

        sections = []
        for s in c.get_display_items():
            # Skip if the section is hidden
            hidden = s.metadata.get('hide_from_toc','false')
            if hidden.lower() == 'true':
                continue

            # Same for sections
            graded = s.metadata.get('graded', False)
            scores = []
            for module in yield_module_descendents(s):
                # course is a module, not a descriptor...
                course_id = course.descriptor.id
                (correct, total) = get_score(course_id, student, module, student_module_cache)
                if correct is None and total is None:
                    continue

                scores.append(Score(correct, total, graded,
                    module.metadata.get('display_name')))

            section_total, graded_total = graders.aggregate_scores(
                scores, s.metadata.get('display_name'))

            format = s.metadata.get('format', "")
            sections.append({
                'display_name': s.display_name,
                'url_name': s.url_name,
                'scores': scores,
                'section_total': section_total,
                'format': format,
                'due': s.metadata.get("due", ""),
                'graded': graded,
            })

        chapters.append({'course': course.display_name,
                         'display_name': c.display_name,
                         'url_name': c.url_name,
                         'sections': sections})

    return chapters


def get_score(course_id, user, problem, student_module_cache):
    """
    Return the score for a user on a problem, as a tuple (correct, total).

    user: a Student object
    problem: an XModule
    cache: A StudentModuleCache
    """
    if not (problem.descriptor.stores_state and problem.descriptor.has_score):
        # These are not problems, and do not have a score
        return (None, None)

    correct = 0.0

    # If the ID is not in the cache, add the item
    instance_module = get_instance_module(course_id, user, problem, student_module_cache)
    # instance_module = student_module_cache.lookup(problem.category, problem.id)
    # if instance_module is None:
    #     instance_module = StudentModule(module_type=problem.category,
    #                                     course_id=????,
    #                                     module_state_key=problem.id,
    #                                     student=user,
    #                                     state=None,
    #                                     grade=0,
    #                                     max_grade=problem.max_score(),
    #                                     done='i')
    #     cache.append(instance_module)
    #     instance_module.save()

    # If this problem is ungraded/ungradable, bail
    if instance_module.max_grade is None:
        return (None, None)

    correct = instance_module.grade if instance_module.grade is not None else 0
    total = instance_module.max_grade

    if correct is not None and total is not None:
        #Now we re-weight the problem, if specified
        weight = getattr(problem, 'weight', None)
        if weight is not None:
            if total == 0:
                log.exception("Cannot reweight a problem with zero weight. Problem: " + str(instance_module))
                return (correct, total)
            correct = correct * weight / total
            total = weight

    return (correct, total)
