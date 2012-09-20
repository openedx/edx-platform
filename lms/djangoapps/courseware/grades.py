# Compute grades using real division, with no integer truncation
from __future__ import division

import random
import logging

from collections import defaultdict
from django.conf import settings
from django.contrib.auth.models import User

from models import StudentModuleCache
from module_render import get_module, get_instance_module
from xmodule import graders
from xmodule.capa_module import CapaModule
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

def yield_dynamic_descriptor_descendents(descriptor, module_creator):
    """
    This returns all of the descendants of a descriptor. If the descriptor
    has dynamic children, the module will be created using module_creator
    and the children (as descriptors) of that module will be returned.
    """
    def get_dynamic_descriptor_children(descriptor):
        if descriptor.has_dynamic_children():
            print "descriptor has dynamic children" , descriptor.location
            module = module_creator(descriptor)
            child_locations = module.get_children_locations()
            return [descriptor.system.load_item(child_location) for child_location in child_locations ]
        else:
            return descriptor.get_children()
    
    
    stack = [descriptor]

    while len(stack) > 0:
        next_descriptor = stack.pop()
        stack.extend( get_dynamic_descriptor_children(next_descriptor) )
        yield next_descriptor
    

def yield_problems(request, course, student):
    """
    Return an iterator over capa_modules that this student has
    potentially answered.  (all that student has answered will definitely be in
    the list, but there may be others as well).
    """
    grading_context = course.grading_context
    student_module_cache = StudentModuleCache(course.id, student, grading_context['all_descriptors'])

    for section_format, sections in grading_context['graded_sections'].iteritems():
        for section in sections:

            section_descriptor = section['section_descriptor']

            # If the student hasn't seen a single problem in the section, skip it.
            skip = True
            for moduledescriptor in section['xmoduledescriptors']:
                if student_module_cache.lookup(
                        course.id, moduledescriptor.category, moduledescriptor.location.url()):
                    skip = False
                    break

            if skip:
                continue

            section_module = get_module(student, request,
                                        section_descriptor.location, student_module_cache,
                                        course.id)
            if section_module is None:
                # student doesn't have access to this module, or something else
                # went wrong.
                # log.debug("couldn't get module for student {0} for section location {1}"
                #           .format(student.username, section_descriptor.location))
                continue

            for problem in yield_module_descendents(section_module):
                if isinstance(problem, CapaModule):
                    yield problem

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
        for capa_module in yield_problems(request, course, student):
            for problem_id in capa_module.lcp.student_answers:
                # Answer can be a list or some other unhashable element.  Convert to string.
                answer = str(capa_module.lcp.student_answers[problem_id])
                key = (capa_module.url_name, capa_module.display_name, problem_id)
                counts[key][answer] += 1

    return counts


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
                
                def create_module(descriptor):
                    # TODO: We need the request to pass into here. If we could forgo that, our arguments
                    # would be simpler
                    return get_module(student, request, descriptor.location, 
                                        student_module_cache, course.id)
                                
                for module_descriptor in yield_dynamic_descriptor_descendents(section_descriptor, create_module):
                                                     
                    (correct, total) = get_score(course.id, student, module_descriptor, create_module, student_module_cache)
                    if correct is None and total is None:
                        continue

                    if settings.GENERATE_PROFILE_SCORES:	# for debugging!
                        if total > 1:
                            correct = random.randrange(max(total - 2, 1), total + 1)
                        else:
                            correct = total

                    graded = module_descriptor.metadata.get("graded", False)
                    if not total > 0:
                        #We simply cannot grade a problem that is 12/0, because we might need it as a percentage
                        graded = False

                    scores.append(Score(correct, total, graded, module_descriptor.metadata.get('display_name')))

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


# TODO: This method is not very good. It was written in the old course style and
# then converted over and performance is not good. Once the progress page is redesigned
# to not have the progress summary this method should be deleted (so it won't be copied).
def progress_summary(student, request, course, grader, student_module_cache):
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
    
    If the student does not have access to load the course module, this function
    will return None.
    
    """
    
    
    # TODO: We need the request to pass into here. If we could forgo that, our arguments
    # would be simpler
    course_module = get_module(student, request,
                                course.location, student_module_cache,
                                course.id)
    if not course_module:
        # This student must not have access to the course.
        return None
    
    chapters = []
    # Don't include chapters that aren't displayable (e.g. due to error)
    for chapter_module in course_module.get_display_items():
        # Skip if the chapter is hidden
        hidden = chapter_module.metadata.get('hide_from_toc','false')
        if hidden.lower() == 'true':
            continue
        
        sections = []
        for section_module in chapter_module.get_display_items():
            # Skip if the section is hidden
            hidden = section_module.metadata.get('hide_from_toc','false')
            if hidden.lower() == 'true':
                continue
            
            # Same for sections
            graded = section_module.metadata.get('graded', False)
            scores = []
            
            module_creator = lambda descriptor : section_module.system.get_module(descriptor.location)
            
            for module_descriptor in yield_dynamic_descriptor_descendents(section_module.descriptor, module_creator):
                
                course_id = course.id
                (correct, total) = get_score(course_id, student, module_descriptor, module_creator, student_module_cache)
                if correct is None and total is None:
                    continue

                scores.append(Score(correct, total, graded,
                    module_descriptor.metadata.get('display_name')))

            section_total, graded_total = graders.aggregate_scores(
                scores, section_module.metadata.get('display_name'))

            format = section_module.metadata.get('format', "")
            sections.append({
                'display_name': section_module.display_name,
                'url_name': section_module.url_name,
                'scores': scores,
                'section_total': section_total,
                'format': format,
                'due': section_module.metadata.get("due", ""),
                'graded': graded,
            })

        chapters.append({'course': course.display_name,
                         'display_name': chapter_module.display_name,
                         'url_name': chapter_module.url_name,
                         'sections': sections})

    return chapters


def get_score(course_id, user, problem_descriptor, module_creator, student_module_cache):
    """
    Return the score for a user on a problem, as a tuple (correct, total).

    user: a Student object
    problem: an XModule
    cache: A StudentModuleCache
    """
    if not (problem_descriptor.stores_state and problem_descriptor.has_score):
        # These are not problems, and do not have a score
        return (None, None)

    correct = 0.0
    
    instance_module = student_module_cache.lookup(
        course_id, problem_descriptor.category, problem_descriptor.location.url())
    
    if not instance_module:
        # If the problem was not in the cache, we need to instantiate the problem.
        # Otherwise, the max score (cached in instance_module) won't be available 
        problem = module_creator(problem_descriptor)
        instance_module = get_instance_module(course_id, user, problem, student_module_cache)

    # If this problem is ungraded/ungradable, bail
    if not instance_module or instance_module.max_grade is None:
        return (None, None)

    correct = instance_module.grade if instance_module.grade is not None else 0
    total = instance_module.max_grade

    if correct is not None and total is not None:
        #Now we re-weight the problem, if specified
        weight = getattr(problem_descriptor, 'weight', None)
        if weight is not None:
            if total == 0:
                log.exception("Cannot reweight a problem with zero weight. Problem: " + str(instance_module))
                return (correct, total)
            correct = correct * weight / total
            total = weight

    return (correct, total)
