import courseware.content_parser as content_parser
import courseware.modules
import logging
import random
import urllib

from collections import namedtuple
from django.conf import settings
from lxml import etree
from models import StudentModule
from student.models import UserProfile

log = logging.getLogger("mitx.courseware")

Score = namedtuple("Score", "earned possible graded section")

def get_grade(user, problem, cache):
    ## HACK: assumes max score is fixed per problem
    id = problem.get('id')
    correct = 0
    
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
            correct=response.grade
        
    # Grab max grade from cache, or if it doesn't exist, compute and save to DB
    if id in cache and response.max_grade != None:
        total = response.max_grade
    else:
        total=courseware.modules.capa_module.Module(etree.tostring(problem), "id").max_score()
        response.max_grade = total
        response.save()

    return (correct, total)

def grade_sheet(student):
    """
    This pulls a summary of all problems in the course. It returns a dictionary with two datastructures:
    
    - courseware_summary is a summary of all sections with problems in the course. It is organized as an array of chapters,
    each containing an array of sections, each containing an array of scores. This contains information for graded and ungraded
    problems, and is good for displaying a course summary with due dates, etc.
    
    - grade_summary is a summary of how the final grade breaks down. It is an array of "sections". Each section can either be
    a conglomerate of scores (like labs or homeworks) which has subscores and a totalscore, or a section can be all from one assignment
    (such as a midterm or final) and only has a totalscore. Each section has a weight that shows how it contributes to the total grade.
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
                    (correct,total) = get_grade(student, p, response_by_id)
                    # id = p.get('id')
                    # correct = 0
                    # if id in response_by_id:
                    #     response = response_by_id[id]
                    #     if response.grade!=None:
                    #         correct=response.grade

                    # total=courseware.modules.capa_module.Module(etree.tostring(p), "id").max_score() # TODO: Add state. Not useful now, but maybe someday problems will have randomized max scores? 
                    # print correct, total
                    if settings.GENERATE_PROFILE_SCORES:
                        if total > 1:
                            correct = random.randrange( max(total-2, 1) , total + 1 )
                        else:
                            correct = total
                    
                    scores.append( Score(int(correct),total, graded, s.get("name")) )

                
                section_total = Score(sum([score.earned for score in scores]), 
                                        sum([score.possible for score in scores]),
                                        False,
                                        p.get("id"))

                graded_total = Score(sum([score.earned for score in scores if score.graded]), 
                                sum([score.possible for score in scores if score.graded]),
                                True,
                                p.get("id"))

                #Add the graded total to totaled_scores
                format = s.get('format') if s.get('format') else ""
                subtitle = s.get('subtitle') if s.get('subtitle') else format
                if format and graded_total[1] > 0:
                    format_scores = totaled_scores.get(format, [])
                    format_scores.append( graded_total )
                    totaled_scores[ format ] = format_scores

                score={'section':s.get("name"),
                       'scores':scores,
                       'section_total' : section_total,
                       'format' : format,
                       'subtitle' : subtitle,
                       'due' : s.get("due") or "",
                       'graded' : graded,
                       }
                sections.append(score)

        chapters.append({'course':course,
                         'chapter' : c.get("name"),
                         'sections' : sections,})
    
    
    grade_summary = grade_summary_6002x(totaled_scores)
    
    return {'courseware_summary' : chapters,
            'grade_summary' : grade_summary}


def grade_summary_6002x(totaled_scores):
    """
    This function takes the a dictionary of (graded) section scores, and applies the course grading rules to create
    the grade_summary. For 6.002x this means homeworks and labs all have equal weight, with the lowest 2 of each
    being dropped. There is one midterm and one final.
    """
    
    def totalWithDrops(scores, drop_count):
        #Note that this key will sort the list descending
        sorted_scores = sorted( enumerate(scores), key=lambda x: -x[1]['percentage'] )
        # A list of the indices of the dropped scores
        dropped_indices = [score[0] for score in sorted_scores[-drop_count:]] 
        aggregate_score = 0
        for index, score in enumerate(scores):
            if index not in dropped_indices:
                aggregate_score += score['percentage']
        
        aggregate_score /= len(scores) - drop_count
        
        return aggregate_score, dropped_indices
        
    #Figure the homework scores
    homework_scores = totaled_scores['Homework'] if 'Homework' in totaled_scores else []
    homework_percentages = []
    for i in range(12):
        if i < len(homework_scores):
            percentage = homework_scores[1].earned / float(homework_scores[i].possible)
            summary = "Homework {0} - {1} - {2:.0%} ({3:g}/{4:g})".format( i + 1, homework_scores[i].section , percentage, homework_scores[i].earned, homework_scores[i].possible )
        else:
            percentage = 0
            summary = "Unreleased Homework {0} - 0% (?/?)".format(i + 1)
        
            if settings.GENERATE_PROFILE_SCORES:
                points_possible = random.randrange(10, 50)
                points_earned = random.randrange(5, points_possible)
                percentage = points_earned / float(points_possible)
                summary = "Random Homework - {0:.0%} ({1:g}/{2:g})".format( percentage, points_earned, points_possible )
        
        label = "HW {0:02d}".format(i + 1)
        
        homework_percentages.append( {'percentage': percentage, 'summary': summary, 'label' : label} )
    homework_total, homework_dropped_indices = totalWithDrops(homework_percentages, 2)
    
    #Figure the lab scores
    lab_scores = totaled_scores['Lab'] if 'Lab' in totaled_scores else []
    lab_percentages = []
    for i in range(12):
        if i < len(lab_scores):
            percentage = lab_scores[i].earned / float(lab_scores[i].possible)
            summary = "Lab {0} - {1} - {2:.0%} ({3:g}/{4:g})".format( i + 1, lab_scores[i].section , percentage, lab_scores[i].earned, lab_scores[i].possible )
        else:
            percentage = 0
            summary = "Unreleased Lab {0} - 0% (?/?)".format(i + 1)
        
            if settings.GENERATE_PROFILE_SCORES:
                points_possible = random.randrange(10, 50)
                points_earned = random.randrange(5, points_possible)
                percentage = points_earned / float(points_possible)
                summary = "Random Lab - {0:.0%} ({1:g}/{2:g})".format( percentage, points_earned, points_possible )
            
        label = "Lab {0:02d}".format(i + 1)
                
        lab_percentages.append( {'percentage': percentage, 'summary': summary, 'label' : label} )
    lab_total, lab_dropped_indices = totalWithDrops(lab_percentages, 2)
    
    
    #TODO: Pull this data about the midterm and final from the databse. It should be exactly similar to above, but we aren't sure how exams will be done yet.
    midterm_score = Score('?', '?', True, "?")
    midterm_percentage = 0
    
    final_score = Score('?', '?', True, "?")
    final_percentage = 0
    
    if settings.GENERATE_PROFILE_SCORES:
        midterm_score = Score(random.randrange(50, 150), 150, True, "?")
        midterm_percentage = midterm_score.earned / float(midterm_score.possible)
        
        final_score = Score(random.randrange(100, 300), 300, True, "?")
        final_percentage = final_score.earned / float(final_score.possible)
        
    
    grade_summary = [
        {
            'category': 'Homework',
            'subscores' : homework_percentages,
            'dropped_indices' : homework_dropped_indices,
            'totalscore' : homework_total,
            'totalscore_summary' : "Homework Average - {0:.0%}".format(homework_total),
            'totallabel' : 'HW Avg',
            'weight' : 0.15,
        },
        {
            'category': 'Labs',
            'subscores' : lab_percentages,
            'dropped_indices' : lab_dropped_indices,
            'totalscore' : lab_total,
            'totalscore_summary' : "Lab Average - {0:.0%}".format(lab_total),
            'totallabel' : 'Lab Avg',
            'weight' : 0.15,
        },
        {
            'category': 'Midterm',
            'totalscore' : midterm_percentage,
            'totalscore_summary' : "Midterm - {0:.0%} ({1}/{2})".format(midterm_percentage, midterm_score.earned, midterm_score.possible),
            'totallabel' : 'Midterm',
            'weight' : 0.30,
        },
        {
            'category': 'Final',
            'totalscore' : final_percentage,
            'totalscore_summary' : "Final - {0:.0%} ({1}/{2})".format(final_percentage, final_score.earned, final_score.possible),
            'totallabel' : 'Final',
            'weight' : 0.40,
        }
    ]
    
    return grade_summary
