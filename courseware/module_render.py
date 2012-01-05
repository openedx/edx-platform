from django.http import HttpResponse
from django.template import Context, loader
from djangomako.shortcuts import render_to_response, render_to_string
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
import html_module
import schematic_module

from models import StudentModule

import urllib

from django.conf import settings

import content_parser

import uuid

modx_modules={'problem':capa_module.LoncapaModule, 
              'video':video_module.VideoModule,
              'html':html_module.HtmlModule,
              'schematic':schematic_module.SchematicModule}

def modx_dispatch(request, module=None, dispatch=None, id=None):
    ''' Generic view for extensions. '''
    s = StudentModule.objects.filter(module_type=module, 
                                     student=request.user, 
                                     module_id=id)
    if len(s) == 0:
        print "ls404"
        raise Http404

    s=s[0]

    dispatch=dispatch.split('?')[0]

    ajax_url = '/modx/'+module+'/'+id+'/'

    id_tag=modx_modules[module].id_attribute

    xml = content_parser.module_xml(content_parser.course_file(request.user), module, id_tag, id)

    instance=modx_modules[module](xml, 
                                  s.module_id, 
                                  ajax_url=ajax_url, 
                                  state=s.state)
    html=instance.handle_ajax(dispatch, request.POST)
    s.state=instance.get_state()
    s.grade=instance.get_score()['score']
    s.save()
    return HttpResponse(html)

def vertical_module(request, module):
    ''' Layout module which lays out content vertically. 
    '''
    contents=[(e.getAttribute("name"),render_module(request, e)) \
              for e in module.childNodes \
              if e.nodeType==1]
    init_js="".join([e[1]['init_js'] for e in contents if 'init_js' in e[1]])
    destroy_js="".join([e[1]['destroy_js'] for e in contents if 'destroy_js' in e[1]])

    return {'init_js':init_js, 
            'destroy_js':destroy_js, 
            'content':render_to_string('vert_module.html',{'items':contents}), 
            'type':'vertical'}

def seq_module(request, module):
    ''' Layout module which lays out content in a temporal sequence
    '''
    def j(m): 
        # jsonify contents so it can be embedded in a js array
        # We also need to split </script> tags so they don't break
        # mid-string
        if 'init_js' not in m: m['init_js']=""
        if 'type' not in m: m['init_js']=""
        content=json.dumps(m['content']) 
        content=content.replace('</script>', '<"+"/script>') 

        return {'content':content, 
                "destroy_js":m['destroy_js'], 
                'init_js':m['init_js'], 
                'type':m['type']}
    contents=[(e.getAttribute("name"),j(render_module(request, e))) \
              for e in module.childNodes \
              if e.nodeType==1]
     
    js=""

    iid=uuid.uuid1().hex

    params={'items':contents,
            'id':"seq"}

    # TODO/BUG: Destroy JavaScript should only be called for the active view
    # This calls it for all the views
    # 
    # To fix this, we'd probably want to have some way of assigning unique
    # IDs to sequences. 
    destroy_js="".join([e[1]['destroy_js'] for e in contents if 'destroy_js' in e[1]])

    if module.nodeName == 'sequential':
        return {'init_js':js+render_to_string('seq_module.js',params),
                "destroy_js":destroy_js,
                'content':render_to_string('seq_module.html',params), 
                'type':'sequential'}
    if module.nodeName == 'tab':
        params['id'] = 'tab'
        return {'init_js':js+render_to_string('tab_module.js',params),
                "destroy_js":destroy_js,
                'content':render_to_string('tab_module.html',params), 
                'type':'tab'}


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
                           state=instance.get_state())
    # Grab content
    content = {'content':instance.get_html(), 
               "destroy_js":instance.get_destroy_js(),
               'init_js':instance.get_init_js(), 
               'type':module_type}

    smod.save() # This may be optional (at least in the case of no instance in the dB)

    return content

module_types={'video':render_x_module,
              'html':render_x_module,
              'tab':seq_module,
              'vertical':vertical_module,
              'sequential':seq_module,
              'problem':render_x_module,
              'schematic':render_x_module
              }

def render_module(request, module):
    ''' Generic dispatch for internal modules. '''
    if module==None:
        return {"content":""}
    if str(module.localName) in module_types:
        return module_types[module.localName](request, module)
    print "rm404"
    raise Http404
