import json
import logging
import os
import random
import sys
import StringIO
import urllib
import uuid

from django.conf import settings
from django.core.context_processors import csrf
from django.contrib.auth.models import User
from django.http import HttpResponse, Http404
from django.shortcuts import redirect
from django.template import Context, loader
from mitxmako.shortcuts import render_to_response, render_to_string
#from django.views.decorators.csrf import ensure_csrf_cookie
from django.db import connection
from django.views.decorators.cache import cache_control

from lxml import etree

from module_render import render_module, modx_dispatch
from models import StudentModule
from student.models import UserProfile

import courseware.content_parser as content_parser
import courseware.modules.capa_module

log = logging.getLogger("mitx.courseware")

etree.set_default_parser(etree.XMLParser(dtd_validation=False, load_dtd=False,
                                         remove_comments = True))

template_imports={'urllib':urllib}

def get_grade(request, problem, cache):
    ## HACK: assumes max score is fixed per problem
    id = problem.get('id')
    correct = 0
    
    # If the ID is not in the cache, add the item
    if id not in cache: 
        module = StudentModule(module_type = 'problem',  # TODO: Move into StudentModule.__init__?
                               module_id = id,
                               student = request.user, 
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

@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def profile(request):
    ''' User profile. Show username, location, etc, as well as grades .
        We need to allow the user to change some of these settings .'''
    if not request.user.is_authenticated():
        return redirect('/')
    
    dom=content_parser.course_file(request.user)
    course = dom.xpath('//course/@name')[0]
    xmlChapters = dom.xpath('//course[@name=$course]/chapter', course=course)

    responses=StudentModule.objects.filter(student=request.user)
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
                    (correct,total) = get_grade(request, p, response_by_id)
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
                    format_scores.append( graded_total )
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
            summary = "{0:.0%} ({1:g}/{2:g})".format( percentage, homework_scores[i][0], homework_scores[i][1] )
        else:
            percentage = 0
            summary = "0% (?/?)"
        
            if settings.GENERATE_PROFILE_SCORES:
                points_possible = random.randrange(10, 50)
                points_earned = random.randrange(5, points_possible)
                percentage = points_earned / float(points_possible)
                summary = "{0:.0%} ({1:g}/{2:g})".format( percentage, points_earned, points_possible )
        
        summary = "Homework {0} - {1}".format(i + 1, summary)
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
            summary = "{0:.0%} ({1:g}/{2:g})".format( percentage, lab_scores[i][0], lab_scores[i][1] )
        else:
            percentage = 0
            summary = "0% (?/?)"
        
            if settings.GENERATE_PROFILE_SCORES:
                points_possible = random.randrange(10, 50)
                points_earned = random.randrange(5, points_possible)
                percentage = points_earned / float(points_possible)
                summary = "{0:.0%} ({1:g}/{2:g})".format( percentage, points_earned, points_possible )
            
        summary = "Lab {0} - {1}".format(i + 1, summary)
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
    
    
    user_info = UserProfile.objects.get(user=request.user) # request.user.profile_cache # 
    context={'name':user_info.name,
             'username':request.user.username,
             'location':user_info.location,
             'language':user_info.language,
             'email':request.user.email,
             'chapters':chapters,
             'format_url_params' : format_url_params,
             'grade_summary' : grade_summary,
             'csrf':csrf(request)['csrf_token']
             }

    return render_to_response('profile.html', context)

def format_url_params(params):
    return [ urllib.quote(string.replace(' ','_')) for string in params ]

def render_accordion(request,course,chapter,section):
    ''' Draws navigation bar. Takes current position in accordion as
        parameter. Returns (initialization_javascript, content)'''
    if not course:
        course = "6.002 Spring 2012"
    
    toc=content_parser.toc_from_xml(content_parser.course_file(request.user), chapter, section)
    active_chapter=1
    for i in range(len(toc)):
        if toc[i]['active']:
            active_chapter=i
    context=dict([['active_chapter',active_chapter],
                  ['toc',toc], 
                  ['course_name',course],
                  ['format_url_params',format_url_params],
                  ['csrf',csrf(request)['csrf_token']]] + \
                     template_imports.items())
    return {'init_js':render_to_string('accordion_init.js',context), 
            'content':render_to_string('accordion.html',context)}

@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def render_section(request, section):
    ''' TODO: Consolidate with index 
    '''
    user = request.user
    if not settings.COURSEWARE_ENABLED or not user.is_authenticated():
        return redirect('/')

#    try: 
    dom = content_parser.section_file(user, section)
    #except:
     #   raise Http404

    accordion=render_accordion(request, '', '', '')

    module_ids = dom.xpath("//@id")
    
    module_object_preload = list(StudentModule.objects.filter(student=user, 
                                                              module_id__in=module_ids))
    
    module=render_module(user, request, dom, module_object_preload)

    if 'init_js' not in module:
        module['init_js']=''

    context={'init':accordion['init_js']+module['init_js'],
             'accordion':accordion['content'],
             'content':module['content'],
             'csrf':csrf(request)['csrf_token']}

    result = render_to_response('courseware.html', context)
    return result


@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def index(request, course="6.002 Spring 2012", chapter="Using the System", section="Hints"): 
    ''' Displays courseware accordion, and any associated content. 
    ''' 
    user = request.user
    if not settings.COURSEWARE_ENABLED or not user.is_authenticated():
        return redirect('/')

    # Fixes URLs -- we don't get funny encoding characters from spaces
    # so they remain readable
    ## TODO: Properly replace underscores
    course=course.replace("_"," ")
    chapter=chapter.replace("_"," ")
    section=section.replace("_"," ")

    # HACK: Force course to 6.002 for now
    # Without this, URLs break
    if course!="6.002 Spring 2012":
        return redirect('/')

    #import logging
    #log = logging.getLogger("mitx")
    #log.info(  "DEBUG: "+str(user) )

    dom = content_parser.course_file(user)
    dom_module = dom.xpath("//course[@name=$course]/chapter[@name=$chapter]//section[@name=$section]/*[1]", 
                           course=course, chapter=chapter, section=section)
    if len(dom_module) == 0:
        module = None
    else:
        module = dom_module[0]

    accordion=render_accordion(request, course, chapter, section)

    module_ids = dom.xpath("//course[@name=$course]/chapter[@name=$chapter]//section[@name=$section]//@id", 
                           course=course, chapter=chapter, section=section)

    module_object_preload = list(StudentModule.objects.filter(student=user, 
                                                              module_id__in=module_ids))
    

    module=render_module(user, request, module, module_object_preload)

    if 'init_js' not in module:
        module['init_js']=''

    context={'init':accordion['init_js']+module['init_js'],
             'accordion':accordion['content'],
             'content':module['content'],
             'csrf':csrf(request)['csrf_token']}

    result = render_to_response('courseware.html', context)
    return result
