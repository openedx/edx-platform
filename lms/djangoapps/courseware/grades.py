"""
Course settings module. The settings are based of django.conf. All settings in
courseware.global_course_settings are first applied, and then any settings
in the settings.DATA_DIR/course_settings.py are applied. A setting must be
in ALL_CAPS.
    
Settings are used by calling
    
from courseware import course_settings

Note that courseware.course_settings is not a module -- it's an object. So 
importing individual settings is not possible:

from courseware.course_settings import GRADER  # This won't work.

"""

from lxml import etree
import random
import imp
import logging
import sys
import types

from django.conf import settings

from courseware import global_course_settings
from xmodule import graders
from xmodule.graders import Score
from models import StudentModule
import courseware.content_parser as content_parser
import xmodule

_log = logging.getLogger("mitx.courseware")

class Settings(object):
    def __init__(self):
        # update this dict from global settings (but only for ALL_CAPS settings)
        for setting in dir(global_course_settings):
            if setting == setting.upper():
                setattr(self, setting, getattr(global_course_settings, setting))
        
        
        data_dir = settings.DATA_DIR
        
        fp = None
        try:
            fp, pathname, description = imp.find_module("course_settings", [data_dir])
            mod = imp.load_module("course_settings", fp, pathname, description)
        except Exception as e:
            _log.exception("Unable to import course settings file from " + data_dir + ". Error: " + str(e))
            mod = types.ModuleType('course_settings')
        finally:
            if fp:
                fp.close()
                
        for setting in dir(mod):
            if setting == setting.upper():
                setting_value = getattr(mod, setting)
                setattr(self, setting, setting_value)
                
        # Here is where we should parse any configurations, so that we can fail early
        self.GRADER = graders.grader_from_conf(self.GRADER)

course_settings = Settings()




def grade_sheet(student,coursename=None):
    """
    This pulls a summary of all problems in the course. It returns a dictionary with two datastructures:
    
    - courseware_summary is a summary of all sections with problems in the course. It is organized as an array of chapters,
    each containing an array of sections, each containing an array of scores. This contains information for graded and ungraded
    problems, and is good for displaying a course summary with due dates, etc.
    
    - grade_summary is the output from the course grader. More information on the format is in the docstring for CourseGrader.
    """
    dom=content_parser.course_file(student,coursename)
    course = dom.xpath('//course/@name')[0]
    xmlChapters = dom.xpath('//course[@name=$course]/chapter', course=course)

    responses=StudentModule.objects.filter(student=student)
    response_by_id = {}
    for response in responses:
        response_by_id[response.module_id] = response
    
    
    totaled_scores = {}
    chapters=[]
    for c in xmlChapters:
        sections = []
        chname=c.get('name')
        
        
        for s in dom.xpath('//course[@name=$course]/chapter[@name=$chname]/section', 
                           course=course, chname=chname):
            problems=dom.xpath('//course[@name=$course]/chapter[@name=$chname]/section[@name=$section]//problem', 
                           course=course, chname=chname, section=s.get('name'))

            graded = True if s.get('graded') == "true" else False
            scores=[]
            if len(problems)>0:
                for p in problems:
                    (correct,total) = get_score(student, p, response_by_id, coursename=coursename)
                    
                    if settings.GENERATE_PROFILE_SCORES:
                        if total > 1:
                            correct = random.randrange( max(total-2, 1) , total + 1 )
                        else:
                            correct = total
                    
                    if not total > 0:
                        #We simply cannot grade a problem that is 12/0, because we might need it as a percentage
                        graded = False 
                    scores.append( Score(correct,total, graded, p.get("name")) )

                section_total, graded_total = graders.aggregate_scores(scores, s.get("name"))
                #Add the graded total to totaled_scores
                format = s.get('format', "")
                subtitle = s.get('subtitle', format)
                if format and graded_total[1] > 0:
                    format_scores = totaled_scores.get(format, [])
                    format_scores.append( graded_total )
                    totaled_scores[ format ] = format_scores

                section_score={'section':s.get("name"),
                       'scores':scores,
                       'section_total' : section_total,
                       'format' : format,
                       'subtitle' : subtitle,
                       'due' : s.get("due") or "",
                       'graded' : graded,
                       }
                sections.append(section_score)

        chapters.append({'course':course,
                         'chapter' : c.get("name"),
                         'sections' : sections,})
    
        
    grader = course_settings.GRADER
    grade_summary = grader.grade(totaled_scores)
    
    return {'courseware_summary' : chapters,
            'grade_summary' : grade_summary}

def get_score(user, problem, cache, coursename=None):
    ## HACK: assumes max score is fixed per problem
    id = problem.get('id')
    correct = 0.0
    
    # If the ID is not in the cache, add the item
    if id not in cache:
        module = StudentModule(module_type = 'problem',  # TODO: Move into StudentModule.__init__?
                               module_id = id,
                               student = user, 
                               state = None, 
                               grade = 0,
                               max_grade = None,
                               done = 'i')
        cache[id] = module

    # Grab the # correct from cache
    if id in cache:
        response = cache[id]
        if response.grade!=None:
            correct=float(response.grade)
        
    # Grab max grade from cache, or if it doesn't exist, compute and save to DB
    if id in cache and response.max_grade is not None:
        total = response.max_grade
    else:
        ## HACK 1: We shouldn't specifically reference capa_module
        ## HACK 2: Backwards-compatibility: This should be written when a grade is saved, and removed from the system
        from module_render import I4xSystem
        system = I4xSystem(None, None, None, coursename=coursename)
        total=float(xmodule.capa_module.Module(system, etree.tostring(problem), "id").max_score())
        response.max_grade = total
        response.save()
        
    #Now we re-weight the problem, if specified
    weight = problem.get("weight", None)
    if weight:
        weight = float(weight) 
        correct = correct * weight / total
        total = weight        

    return (correct, total)
