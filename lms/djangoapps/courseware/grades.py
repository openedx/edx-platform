import random
import logging

from django.conf import settings

from module_render import get_module
from xmodule import graders
from xmodule.graders import Score
from models import StudentModule

_log = logging.getLogger("mitx.courseware")





def get_graded_sections(course_descriptor):
    """
    Arguments:
        course_descriptor: a CourseDescriptor object for the course to be graded
        
    Returns:
        A dictionary keyed by section-type. The values are arrays of dictionaries containing
            "section_descriptor" : The section descriptor
            "xmoduledescriptors" : An array of xmoduledescriptors that could possibly be in the section, for any student
    """
    
    graded_sections = {}
    for c in course_descriptor.get_children():
        sections = []
        for s in c.get_children():
            if s.metadata.get('graded', False):
                
                xmoduledescriptors = []
                for module in yield_descriptor_descendents(s):
                    xmoduledescriptors.append(module)
                    
                section_description = { 'section_descriptor' : s, 'xmoduledescriptors' : xmoduledescriptors}
                
                section_format = s.metadata.get('format', "")
                graded_sections[ section_format ] = graded_sections.get( section_format, [] ) + [section_description]
    
    return graded_sections

def yield_descriptor_descendents(module_descriptor):
    for child in module_descriptor.get_children():
        yield child
        for module_descriptor in yield_descriptor_descendents(child):
            yield module_descriptor

def yield_module_descendents(module):
    for child in module.get_display_items():
        yield child
        for module in yield_module_descendents(child):
            yield module
   
def fast_grade(student, request, course_graded_sections, grader, student_module_cache):
    totaled_scores = {}
    for section_format, sections in course_graded_sections.iteritems():
        format_scores = []
        for section in sections:
            section_descriptor = section['section_descriptor']
            section_name = section_descriptor.metadata.get('display_name')
            
            should_grade_section = False
            # If we haven't seen a single problem in the section, we don't have to grade it at all! We can assume 0%
            for moduledescriptor in section['xmoduledescriptors']:
                if student_module_cache.lookup(moduledescriptor.category, moduledescriptor.location.url() ):
                    should_grade_section = True
                    break
            
            if should_grade_section:
                scores = []
                (section_module, _, _, _) = get_module(student, request, section_descriptor.location, student_module_cache)
                
                for module in yield_descriptor_descendents(section_module):
                    (correct, total) = get_score(student, module, student_module_cache)
                    graded = module.metadata.get("graded", False)

                    if correct is None and total is None:
                        continue

                    if settings.GENERATE_PROFILE_SCORES:
                        if total > 1:
                            correct = random.randrange(max(total - 2, 1), total + 1)
                        else:
                            correct = total

                    if not total > 0:
                        #We simply cannot grade a problem that is 12/0, because we might need it as a percentage
                        graded = False
                    
                    scores.append(Score(correct, total, graded, module.metadata.get('display_name')))
                    
                section_total, graded_total = graders.aggregate_scores(scores, section_name)
            else:
                section_total = Score(0.0, 1.0, False, section_name)
                graded_possible = 1.0 #if s.metadata.get("graded", False) else 0.0
                graded_total = Score(0.0, graded_possible, True, section_name)
                
            #Add the graded total to totaled_scores
            if graded_total.possible > 0:
                format_scores.append(graded_total)
        
        totaled_scores[section_format] = format_scores
    
    grade_summary = grade_summary = grader.grade(totaled_scores)
    return grade_summary
    

def grade_sheet(student, course, grader, student_module_cache):
    """
    This pulls a summary of all problems in the course. It returns a dictionary with two datastructures:

    - courseware_summary is a summary of all sections with problems in the course. It is organized as an array of chapters,
    each containing an array of sections, each containing an array of scores. This contains information for graded and ungraded
    problems, and is good for displaying a course summary with due dates, etc.

    - grade_summary is the output from the course grader. More information on the format is in the docstring for CourseGrader.

    Arguments:
        student: A User object for the student to grade
        course: An XModule containing the course to grade
        student_module_cache: A StudentModuleCache initialized with all instance_modules for the student
    """
    totaled_scores = {}
    chapters = []
    for c in course.get_children():
        sections = []
        for s in c.get_children():
            graded = s.metadata.get('graded', False)
            scores = []
            for module in yield_module_descendents(s):
                (correct, total) = get_score(student, module, student_module_cache)

                if correct is None and total is None:
                    continue

                if settings.GENERATE_PROFILE_SCORES:
                    if total > 1:
                        correct = random.randrange(max(total - 2, 1), total + 1)
                    else:
                        correct = total

                if not total > 0:
                    #We simply cannot grade a problem that is 12/0, because we might need it as a percentage
                    graded = False

                scores.append(Score(correct, total, graded, module.metadata.get('display_name')))

            section_total, graded_total = graders.aggregate_scores(scores, s.metadata.get('display_name'))
            #Add the graded total to totaled_scores
            format = s.metadata.get('format', "")
            if format and graded_total.possible > 0:
                format_scores = totaled_scores.get(format, [])
                format_scores.append(graded_total)
                totaled_scores[format] = format_scores

            sections.append({
                'section': s.metadata.get('display_name'),
                'scores': scores,
                'section_total': section_total,
                'format': format,
                'due': s.metadata.get("due", ""),
                'graded': graded,
            })

        chapters.append({'course': course.metadata.get('display_name'),
                         'chapter': c.metadata.get('display_name'),
                         'sections': sections})

    grade_summary = grader.grade(totaled_scores)

    return {'courseware_summary': chapters,
            'grade_summary': grade_summary}


def get_score(user, problem, cache):
    """
    Return the score for a user on a problem

    user: a Student object
    problem: an XModule
    cache: A StudentModuleCache
    """
    correct = 0.0

    # If the ID is not in the cache, add the item
    instance_module = cache.lookup(problem.category, problem.id)
    if instance_module is None:
        instance_module = StudentModule(module_type=problem.category,
                                        module_state_key=problem.id,
                                        student=user,
                                        state=None,
                                        grade=0,
                                        max_grade=problem.max_score(),
                                        done='i')
        cache.append(instance_module)
        instance_module.save()

    # If this problem is ungraded/ungradable, bail
    if instance_module.max_grade is None:
        return (None, None)

    correct = instance_module.grade if instance_module.grade is not None else 0
    total = instance_module.max_grade

    if correct is not None and total is not None:
        #Now we re-weight the problem, if specified
        weight = getattr(problem, 'weight', 1)
        if weight != 1:
            correct = correct * weight / total
            total = weight

    return (correct, total)
