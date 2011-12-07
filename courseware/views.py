from django.http import HttpResponse
from django.template import Context, loader
from djangomako.shortcuts import render_to_response, render_to_string
from xml.dom.minidom import parse, parseString
import json, os, sys
from django.core.context_processors import csrf

from django.template import Context
from django.contrib.auth.models import User
from auth.models import UserProfile
from django.shortcuts import redirect

import StringIO

from django.http import Http404

import urllib

import capa_module, capa_problem

from models import StudentModule

import urllib

from django.conf import settings

from content_parser import *

template_imports={'urllib':urllib}

def profile(request):
    if not request.user.is_authenticated():
        return redirect('/')

    dom=parse(settings.DATA_DIR+'course.xml')
    hw=[]
    course = dom.getElementsByTagName('course')[0]
    chapters = course.getElementsByTagName('chapter')

    responses=StudentModule.objects.filter(student=request.user)

    for c in chapters:
        for s in c.getElementsByTagName('section'):
            problems=s.getElementsByTagName('problem')
            scores=[]
            if len(problems)>0:
                for p in problems:
                    id = p.getAttribute('filename')
                    correct = 0
                    for response in responses:
                        if response.module_id == id:
                            if response.grade!=None:
                                correct=response.grade
                            else:
                                correct=0
                    total=capa_module.LoncapaModule(p, id=id).max_score()
                    scores.append((int(correct),total))
                score={'course':course.getAttribute('name'),
                       'section':s.getAttribute("name"),
                       'chapter':c.getAttribute("name"),
                       'scores':scores,
                       }
                hw.append(score)

    user_info=UserProfile.objects.get(user=request.user)

    context={'name':user_info.name,
             'username':request.user.username,
             'location':user_info.location,
             'language':user_info.language,
             'email':request.user.email,
             'homeworks':hw
             }
    return render_to_response('profile.html', context)

def render_accordion(request,course,chapter,section):
    ''' Draws accordion. Takes current position in accordion as
        parameter. Returns (initialization_javascript, content)'''
    def format_string(string):
        return urllib.quote(string.replace(' ','_'))

    toc=toc_from_xml(chapter, section)
    active_chapter=1
    for i in range(len(toc)):
        if toc[i]['active']:
            active_chapter=i
    context=dict([['active_chapter',active_chapter],
                  ['toc',toc], 
                  ['course_name',course],
                  ['format_string',format_string]]+ \
                     template_imports.items())
    return {'js':render_to_string('accordion_init.js',context), 
            'content':render_to_string('accordion.html',context)}

def video_module(request, module):
    id=module.getAttribute('youtube')
    return {'js':render_to_string('video_init.js',{'id':id}), 
            'content':render_to_string('video.html',{})}

def html_module(request, module):
    template_source=module.getAttribute('filename')
    return {'content':render_to_string(template_source, {})}

def tab_module(request, module):
    contents=[(e.getAttribute("name"),render_module(request, e)) \
              for e in module.childNodes \
              if e.nodeType==1]
    js="".join([e[1]['js'] for e in contents if 'js' in e[1]])

    return {'js':render_to_string('tab_module.js',{'tabs':contents})+js, 
            'content':render_to_string('tab_module.html',{'tabs':contents})}

def vertical_module(request, module):
    contents=[(e.getAttribute("name"),render_module(request, e)) \
              for e in module.childNodes \
              if e.nodeType==1]
    js="".join([e[1]['js'] for e in contents if 'js' in e[1]])

    return {'js':js, 
            'content':render_to_string('vert_module.html',{'items':contents})}

def render_x_module(request, xml_module):
    # Check if problem has an instance in DB
    module_id=xml_module.getAttribute(capa_module.LoncapaModule.id_attribute)
    s = StudentModule.objects.filter(student=request.user, module_id=module_id)
    if len(s) == 0:
        # If not, create one, and save it
        problem=capa_module.LoncapaModule(xml_module.toxml(), module_id)
        smod=StudentModule(student=request.user, 
                           module_id=module_id, 
                           state=problem.get_state())
        smod.save()
    elif len(s) == 1:
        # If so, render it
        problem=capa_module.LoncapaModule(xml_module.toxml(), 
                                          module_id, 
                                          state=s[0].state)
    else:
        raise Exception("Database is inconsistent (1).")

    return {'content':problem.get_html()}

def modx_dispatch(request, dispatch=None, id=None):
    s = StudentModule.objects.filter(student=request.user, module_id=id)
    if len(s) == 0:
        raise Http404

    if dispatch=='problem_check': 
        return check_problem(request)
    elif dispatch=='problem_reset':
        return reset_problem(request,id)
    else: 
        print "AAA"
        raise Http404


def reset_problem(request,id):
    s = StudentModule.objects.filter(student=request.user, module_id=id)
    s[0].delete()
    return HttpResponse(json.dumps({}), mimetype="application/json")

def check_problem(request):
    answer=dict()
    # input_resistor_1 ==> resistor_1
    for key in request.GET:
        answer['_'.join(key.split('_')[1:])]=request.GET[key]
    ## THE NEXT TWO LINES ARE SUBTLE, AND CAN EASILY INTRODUCE SECURITY ISSUES
    # 
    # The filename is grabbed from the user. The user could inject arbitrary 
    # filenames and potentially compromise our system. The second line prevents
    # this, since we confirm filename is a valid module_id in the database. 
    # Small changes to the code or to the database could break this. 
    # 
    # We should probably add an explicit check to make sure the filename is in 
    # the XML file to make this less fragile. 
    filename=answer.keys()[0].split('_')[0] 
    s = StudentModule.objects.filter(student=request.user, module_id=filename)

    if len(s) == 1:
        s=s[0]
        problem=capa_problem.LoncapaProblem(settings.DATA_DIR+filename+'.xml', 
                                            id=filename, 
                                            state=s.state)
        js=json.dumps(problem.grade_answers(answer))
        s.state=problem.get_state()
        s.grade=problem.get_score()['score']
        s.save()
    else:
        raise Exception("Database is inconsistent (3).")

    return HttpResponse(js, mimetype="application/json")

module_types={'video':video_module,
              'html':html_module,
              'tab':tab_module,
              'vertical':vertical_module,
              'problem':render_x_module}
                  #'lab':lab_module,

def render_module(request, module):
    if module==None:
        return {"content":""}
    if str(module.localName) in module_types:
        return module_types[module.localName](request, module)
    return {"content":""}

def dom_select(dom, element_type, element_name):
    if dom==None:
        return None
    elements=dom.getElementsByTagName(element_type)
    for e in elements:
        if e.getAttribute("name")==element_name:
            return e
    return None

def index(request, course="6.002 Spring 2012", chapter="Using the System", section="Hints"): 
    if not request.user.is_authenticated():
        return redirect('/')

    # Fix URLs
    course=course.replace("_"," ")
    chapter=chapter.replace("_"," ")
    section=section.replace("_"," ")

    # HACK: Force course to 6.002 for now
    # Without this, URLs break
    if course!="6.002 Spring 2012":
        return redirect('/')

    dom=parse(settings.DATA_DIR+'course.xml')
    dom_course=dom_select(dom, 'course', course)
    dom_chapter=dom_select(dom_course, 'chapter', chapter)
    dom_section=dom_select(dom_chapter, 'section', section)
    if dom_section!=None:
        module=[e for e in dom_section.childNodes if e.nodeType==1][0]
    else:
        module=None

    accordion=render_accordion(request, course, chapter, section)

    module=render_module(request, module)

    if 'js' not in module:
        module['js']=''

    context={'init':accordion['js']+module['js'],
             'accordion':accordion['content'],
             'content':module['content']}
    return render_to_response('courseware.html', context)


