from lxml import etree
import random

from django.conf import settings

from courseware import course_settings
import courseware.content_parser as content_parser
from courseware.graders import Score
import courseware.modules
from models import StudentModule

def grade_sheet(student):
    """
    This pulls a summary of all problems in the course. It returns a dictionary with two datastructures:
    
    - courseware_summary is a summary of all sections with problems in the course. It is organized as an array of chapters,
    each containing an array of sections, each containing an array of scores. This contains information for graded and ungraded
    problems, and is good for displaying a course summary with due dates, etc.
    
    - grade_summary is the output from the course grader. More information on the format is in the docstring for CourseGrader.
    
    - grade is a letter grade, either 'A', 'B', 'C', or None
    """
    dom=content_parser.course_file(student)
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
                    (correct,total) = get_score(student, p, response_by_id)
                    
                    if settings.GENERATE_PROFILE_SCORES:
                        if total > 1:
                            correct = random.randrange( max(total-2, 1) , total + 1 )
                        else:
                            correct = total
                    
                    if not total > 0:
                        #We simply cannot grade a problem that is 12/0, because we might need it as a percentage
                        graded = False 
                    scores.append( Score(correct,total, graded, p.get("name")) )

                section_total, graded_total = aggregate_scores(scores, s.get("name"))
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
    
    letter_grade = grade_for_percentage(grade_summary['percent'])
    
    _log.debug("Final grade: " + str(letter_grade))
    
    return {'courseware_summary' : chapters,
            'grade_summary' : grade_summary,
            'grade' : letter_grade}
            

def grade_for_percentage(percentage):
    letter_grade = None
    for possible_grade in ['A', 'B', 'C']:
        if percentage >= course_settings.GRADE_CUTOFFS[possible_grade]:
            letter_grade = possible_grade
            break
    
    return letter_grade

def aggregate_scores(scores, section_name = "summary"):    
    total_correct_graded = sum(score.earned for score in scores if score.graded)
    total_possible_graded = sum(score.possible for score in scores if score.graded)
    
    total_correct = sum(score.earned for score in scores)
    total_possible = sum(score.possible for score in scores)
        
    #regardless of whether or not it is graded
    all_total = Score(total_correct, 
                          total_possible,
                          False,
                          section_name)
    #selecting only graded things
    graded_total = Score(total_correct_graded, 
                         total_possible_graded, 
                         True, 
                         section_name)

    return all_total, graded_total
    

def get_score(user, problem, cache):
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
    if id in cache and response.max_grade != None:
        total = response.max_grade
    else:
        total=float(courseware.modules.capa_module.Module(etree.tostring(problem), "id").max_score())
        response.max_grade = total
        response.save()
        
    #Now we re-weight the problem, if specified
    weight = problem.get("weight", None)
    if weight:
        weight = float(weight) 
        correct = correct * weight / total
        total = weight        

    return (correct, total)
