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
from django_future.csrf import ensure_csrf_cookie

from lxml import etree

from module_render import render_module, modx_dispatch
from models import StudentModule
from student.models import UserProfile

import courseware.content_parser as content_parser
import courseware.modules.capa_module

import courseware.grades as grades

log = logging.getLogger("mitx.courseware")

etree.set_default_parser(etree.XMLParser(dtd_validation=False, load_dtd=False,
                                         remove_comments = True))

template_imports={'urllib':urllib}

@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def gradebook(request):
    if 'course_admin' not in content_parser.user_groups(request.user):
        raise Http404
    student_objects = User.objects.all()[:100]
    student_info = [{'username' :s.username,
                     'id' : s.id,
                     'email': s.email,
                     'grade_info' : grades.grade_sheet(s), 
                     'realname' : UserProfile.objects.get(user = s).name,
                     } for s in student_objects]

    return render_to_response('gradebook.html',
        {'students':student_info,
        'grade_cutoffs' : course_settings.GRADE_CUTOFFS,}
    )

@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def profile(request, student_id = None):
    ''' User profile. Show username, location, etc, as well as grades .
        We need to allow the user to change some of these settings .'''
    if not request.user.is_authenticated():
        return redirect('/')

    if student_id == None:
        student = request.user
    else: 
        print content_parser.user_groups(request.user)
        if 'course_admin' not in content_parser.user_groups(request.user):
            raise Http404
        student = User.objects.get( id = int(student_id))

    user_info = UserProfile.objects.get(user=student) # request.user.profile_cache # 

    context={'name':user_info.name,
             'username':student.username,
             'location':user_info.location,
             'language':user_info.language,
             'email':student.email,
             'format_url_params' : content_parser.format_url_params,
             'csrf':csrf(request)['csrf_token'],
             'grade_cutoffs' : course_settings.GRADE_CUTOFFS,
             'grade_sheet' : grades.grade_sheet(student),
             }

    return render_to_response('profile.html', context)

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
                  ['format_url_params',content_parser.format_url_params],
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

@ensure_csrf_cookie
def certificate_request(request):
    ''' Attempt to send a certificate. '''
    if request.method != "POST":
        raise Http404
    
    verification_checked = request.POST.get('cert_request_verify', 'false')
    destination_email = request.POST.get('cert_request_email', '')
    error = ''
    
    if verification_checked != 'true':
        error += 'You must verify that you have followed the honor code to receive a certificate. '
    
    # TODO: Check e-mail format is correct. 
    if len(destination_email) < 5:
        error += 'Please provide a valid email address to send the certificate. '
        
    grade = None
    if len(error) == 0:
        student_gradesheet = grades.grade_sheet(request.user)
        
        grade = student_gradesheet['grade']
        
        if not grade:
            error += 'You have not earned a grade in this course. '
            
    if len(error) == 0:
        # TODO: Send the certificate email
        return HttpResponse(json.dumps({'success':True,
                                        'value': 'A certificate is being generated and will be sent. ' }))
    else:
        return HttpResponse(json.dumps({'success':False,
                                        'error': error }))