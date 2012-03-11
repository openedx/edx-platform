import logging
import urllib
from lxml import etree

import courseware.content_parser as content_parser
from models import StudentModule
from django.conf import settings
import courseware.modules

from student.models import UserProfile

log = logging.getLogger("mitx.courseware")

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
    dom=content_parser.course_file(student)
    course = dom.xpath('//course/@name')[0]
    xmlChapters = dom.xpath('//course[@name=$course]/chapter', course=course)

    responses=StudentModule.objects.filter(student=student)
    response_by_id = {}
    for response in responses:
        response_by_id[response.module_id] = response
    
    
    total_scores = {}
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
                    
                    scores.append((int(correct),total, graded ))


                section_total = (sum([score[0] for score in scores]), 
                                sum([score[1] for score in scores]))

                graded_total = (sum([score[0] for score in scores if score[2]]), 
                                sum([score[1] for score in scores if score[2]]))

                #Add the graded total to total_scores
                format = s.get('format') if s.get('format') else ""
                subtitle = s.get('subtitle') if s.get('subtitle') else format
                if format and graded_total[1] > 0:
                    format_scores = total_scores[ format ] if format in total_scores else []
                    format_scores.append( graded_total + (s.get("name"),) )
                    total_scores[ format ] = format_scores

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
    homework_scores = total_scores['Homework'] if 'Homework' in total_scores else []
    homework_percentages = []
    for i in range(12):
        if i < len(homework_scores):
            percentage = homework_scores[i][0] / float(homework_scores[i][1])
            summary = "Homework {0} - {1} - {2:.0%} ({3:g}/{4:g})".format( i + 1, homework_scores[i][2] , percentage, homework_scores[i][0], homework_scores[i][1] )
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
    lab_scores = total_scores['Lab'] if 'Lab' in total_scores else []
    lab_percentages = []
    log.debug("lab_scores: {0}".format(lab_scores))
    for i in range(12):
        if i < len(lab_scores):
            percentage = lab_scores[i][0] / float(lab_scores[i][1])
            summary = "Lab {0} - {1} - {2:.0%} ({3:g}/{4:g})".format( i + 1, lab_scores[i][2] , percentage, lab_scores[i][0], lab_scores[i][1] )
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
    midterm_score = ('?', '?')
    midterm_percentage = 0
    
    final_score = ('?', '?')
    final_percentage = 0
    
    if settings.GENERATE_PROFILE_SCORES:
        midterm_score = (random.randrange(50, 150), 150)
        midterm_percentage = midterm_score[0] / float(midterm_score[1])
        
        final_score = (random.randrange(100, 300), 300)
        final_percentage = final_score[0] / float(final_score[1])
        
    
    grade_summary = [
        {
            'category': 'Homework',
            'subscores' : homework_percentages,
            'dropped_indices' : homework_dropped_indices,
            'totalscore' : {'score' : homework_total, 'summary' : "Homework Average - {0:.0%}".format(homework_total)},
            'totallabel' : 'HW Avg',
            'weight' : 0.15,
        },
        {
            'category': 'Labs',
            'subscores' : lab_percentages,
            'dropped_indices' : lab_dropped_indices,
            'totalscore' : {'score' : lab_total, 'summary' : "Lab Average - {0:.0%}".format(lab_total)},
            'totallabel' : 'Lab Avg',
            'weight' : 0.15,
        },
        {
            'category': 'Midterm',
            'totalscore' : {'score' : midterm_percentage, 'summary' : "Midterm - {0:.0%} ({1}/{2})".format(midterm_percentage, midterm_score[0], midterm_score[1])},
            'totallabel' : 'Midterm',
            'weight' : 0.30,
        },
        {
            'category': 'Final',
            'totalscore' : {'score' : final_percentage, 'summary' : "Final - {0:.0%} ({1}/{2})".format(final_percentage, final_score[0], final_score[1])},
            'totallabel' : 'Final',
            'weight' : 0.40,
        }
    ]
    
    return {'grade_summary' : grade_summary,
            'chapters':chapters}

    
