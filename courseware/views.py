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

import capa_module
import video_module

from models import StudentModule

import urllib

from django.conf import settings

import content_parser

import uuid

template_imports={'urllib':urllib}

def profile(request):
    ''' User profile. Show username, location, etc, as well as grades .
        We need to allow the user to change some of these settings .'''
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
                    total=capa_module.LoncapaModule(p.toxml(), "id").max_score() # TODO: Add state. Not useful now, but maybe someday problems will have randomized max scores? 
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
             'homeworks':hw, 
             'csrf':csrf(request)['csrf_token']
             }
    return render_to_response('profile.html', context)

def render_accordion(request,course,chapter,section):
    ''' Draws navigation bar. Takes current position in accordion as
        parameter. Returns (initialization_javascript, content)'''
    def format_string(string):
        return urllib.quote(string.replace(' ','_'))

    toc=content_parser.toc_from_xml(chapter, section)
    active_chapter=1
    for i in range(len(toc)):
        if toc[i]['active']:
            active_chapter=i
    context=dict([['active_chapter',active_chapter],
                  ['toc',toc], 
                  ['course_name',course],
                  ['format_string',format_string]]+ \
                     template_imports.items())
    return {'init_js':render_to_string('accordion_init.js',context), 
            'content':render_to_string('accordion.html',context)}

def html_module(request, module):
    ''' Show basic text
    '''
    template_source=module.getAttribute('filename')
    return {'content':render_to_string(template_source, {})}

def vertical_module(request, module):
    ''' Layout module which lays out content vertically. 
    '''
    contents=[(e.getAttribute("name"),render_module(request, e)) \
              for e in module.childNodes \
              if e.nodeType==1]
    js="".join([e[1]['init_js'] for e in contents if 'init_js' in e[1]])

    return {'init_js':js, 
            'content':render_to_string('vert_module.html',{'items':contents})}

def seq_module(request, module):
    ''' Layout module which lays out content in a temporal sequence
    '''
    def j(m): 
        # jsonify contents so it can be embedded in a js array
        # We also need to split </script> tags so they don't break
        # mid-string
        if 'init_js' not in m: m['init_js']=""
        content=json.dumps(m['content']) 
        content=content.replace('</script>', '<"+"/script>') 
        return {'content':content, 'init_js':m['init_js']}
    contents=[(e.getAttribute("name"),j(render_module(request, e))) \
              for e in module.childNodes \
              if e.nodeType==1]
     
    js="".join([e[1]['init_js'] for e in contents if 'init_js' in e[1]])

    iid=uuid.uuid1().hex

    params={'items':contents,
            'id':"seq"}

    print module.nodeName
    if module.nodeName == 'sequential':
        return {'init_js':js+render_to_string('seq_module.js',params),
                'content':render_to_string('seq_module.html',params)}
    if module.nodeName == 'tab':
        return {'init_js':js+render_to_string('tab_module.js',params),
                'content':render_to_string('tab_module.html',params)}


modx_modules={'problem':capa_module.LoncapaModule, 'video':video_module.VideoModule}

def render_x_module(request, xml_module):
    ''' Generic module for extensions. This renders to HTML. '''
    # Check if problem has an instance in DB
    module_type=xml_module.nodeName
    module_class=modx_modules[module_type]
    module_id=xml_module.getAttribute(module_class.id_attribute)
    
    # Grab state from database
    s = StudentModule.objects.filter(student=request.user, 
                                     module_id=module_id, 
                                     module_type = module_type)
    if len(s) == 0: # If nothing in the database...
        state=None
    else:
        smod = s[0]
        state = smod.state

    # Create a new instance
    ajax_url = '/modx/'+module_type+'/'+module_id+'/'
    instance=module_class(xml_module.toxml(), 
                          module_id, 
                          ajax_url=ajax_url,
                          state=state)
    
    # If instance wasn't already in the database, create it
    if len(s) == 0:
        smod=StudentModule(student=request.user, 
                           module_type = module_type,
                           module_id=module_id, 
                           state=instance.get_state(), 
                           xml=instance.xml)
    # Grab content
    content = {'content':instance.get_html(), 
               'init_js':instance.get_init_js()}

    smod.save() # This may be optional (at least in the case of no instance in the dB)

    return content

def modx_dispatch(request, module=None, dispatch=None, id=None):
    ''' Generic module for extensions. '''
    s = StudentModule.objects.filter(module_type=module, student=request.user, module_id=id)
    if len(s) == 0:
        raise Http404

    s=s[0]

    dispatch=dispatch.split('?')[0]

    ajax_url = '/modx/'+module+'/'+id+'/'

    instance=modx_modules[module](s.xml, s.module_id, ajax_url=ajax_url, state=s.state)
    html=instance.handle_ajax(dispatch, request.GET)
    s.state=instance.get_state()
    s.grade=instance.get_score()['score']
    s.save()
    return HttpResponse(html)

module_types={'video':render_x_module,
              'html':html_module,
              'tab':seq_module,
              'vertical':vertical_module,
              'sequential':seq_module,
              'problem':render_x_module,
              }
                  #'lab':lab_module,

def render_module(request, module):
    ''' Generic dispatch for internal modules. '''
    if module==None:
        return {"content":""}
    if str(module.localName) in module_types:
        return module_types[module.localName](request, module)
    return {"content":""}

def index(request, course="6.002 Spring 2012", chapter="Using the System", section="Hints"): 
    ''' Displays courseware accordion, and any associated content. 
    ''' 
    if not request.user.is_authenticated():
        return redirect('/')

    # Fixes URLs -- we don't get funny encoding characters from spaces
    # so they remain readable
    course=course.replace("_"," ")
    chapter=chapter.replace("_"," ")
    section=section.replace("_"," ")

    # HACK: Force course to 6.002 for now
    # Without this, URLs break
    if course!="6.002 Spring 2012":
        return redirect('/')

    dom=parse(settings.DATA_DIR+'course.xml')
    dom_course=content_parser.dom_select(dom, 'course', course)
    dom_chapter=content_parser.dom_select(dom_course, 'chapter', chapter)
    dom_section=content_parser.dom_select(dom_chapter, 'section', section)
    if dom_section!=None:
        module=[e for e in dom_section.childNodes if e.nodeType==1][0]
    else:
        module=None

    accordion=render_accordion(request, course, chapter, section)

    module=render_module(request, module)

    if 'init_js' not in module:
        module['init_js']=''

    context={'init':accordion['init_js']+module['init_js'],
             'accordion':accordion['content'],
             'content':module['content']}
    return render_to_response('courseware.html', context)


