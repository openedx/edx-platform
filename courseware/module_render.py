from django.http import HttpResponse
from django.template import Context, loader
from djangomako.shortcuts import render_to_response, render_to_string
import json, os, sys
from django.core.context_processors import csrf

from django.db import connection
from django.template import Context
from django.contrib.auth.models import User
from auth.models import UserProfile
from django.shortcuts import redirect

import StringIO
import track.views

from django.http import Http404

import urllib

import courseware.modules.capa_module
import courseware.modules.video_module
import courseware.modules.vertical_module
import courseware.modules.html_module
import courseware.modules.schematic_module
import courseware.modules.seq_module

from models import StudentModule

import urllib

from django.conf import settings

import courseware.content_parser as content_parser

import sys

from lxml import etree
import uuid

## TODO: Add registration mechanism
modx_modules={'problem':courseware.modules.capa_module.LoncapaModule, 
              'video':courseware.modules.video_module.VideoModule,
              'html':courseware.modules.html_module.HtmlModule,
              'vertical':courseware.modules.vertical_module.VerticalModule,
              'sequential':courseware.modules.seq_module.SequentialModule,
              'schematic':courseware.modules.schematic_module.SchematicModule}

def object_cache(cache, user, module_type, module_id):
    # We don't look up on user -- all queries include user
    # Additional lookup would require a DB hit the way Django 
    # is broken. 
    for o in cache: 
        if o.module_type == module_type and \
                o.module_id == module_id:
            return o
    return None

def make_track_function(request):
    def f(event_type, event):
        return track.views.server_track(request, event_type, event, page='x_module')
    return f

def modx_dispatch(request, module=None, dispatch=None, id=None):
    ''' Generic view for extensions. '''
    # Grab the student information for the module from the database
    s = StudentModule.objects.filter(module_type=module, 
                                     student=request.user, 
                                     module_id=id)
    if len(s) == 0:
        print "ls404", module, request.user, id
        raise Http404

    s=s[0]

    dispatch=dispatch.split('?')[0]

    ajax_url = '/modx/'+module+'/'+id+'/'

    id_tag=modx_modules[module].id_attribute

    # Grab the XML corresponding to the request from course.xml
    xml = content_parser.module_xml(content_parser.course_file(request.user), module, id_tag, id)

    # Create the module
    instance=modx_modules[module](xml, 
                                  s.module_id, 
                                  ajax_url=ajax_url, 
                                  state=s.state, 
                                  track_function = make_track_function(request), 
                                  render_function = None)
    # Let the module handle the AJAX
    ajax_return=instance.handle_ajax(dispatch, request.POST)
    # Save the state back to the database
    s.state=instance.get_state()
    if instance.get_score() != None: 
        s.grade=instance.get_score()['score']
    s.save()
    # Return whatever the module wanted to return to the client/caller
    return HttpResponse(ajax_return)

def render_x_module(user, request, xml_module, module_object_preload):
    ''' Generic module for extensions. This renders to HTML. '''
    # Check if problem has an instance in DB
    module_type=xml_module.tag
    module_class=modx_modules[module_type]
    module_id=xml_module.get('id') #module_class.id_attribute) or "" 

    # Grab state from database
    #s = object_cache(module_object_preload, 
    #                 user, 
    #                 module_type, 
    #                 module_id)
    s = StudentModule.objects.filter(student=request.user, 
                                     module_id=module_id, 
                                     module_type = module_type)
    if len(s) == 0: 
        s=None
    else:
        s=s[0]

    if s == None: # If nothing in the database...
        state=None
    else:
        smod = s
        state = smod.state

    # Create a new instance
    ajax_url = '/modx/'+module_type+'/'+module_id+'/'
    instance=module_class(etree.tostring(xml_module), 
                          module_id, 
                          ajax_url=ajax_url,
                          state=state, 
                          track_function = make_track_function(request), 
                                  render_function = lambda x: render_module(user, request, x, module_object_preload))
    
    # If instance wasn't already in the database, create it
    if s == None:
        smod=StudentModule(student=user, 
                           module_type = module_type,
                           module_id=module_id, 
                           state=instance.get_state())
        smod.save() # This may be optional (at least in the case of no instance in the dB)
    # Grab content
    content = {'content':instance.get_html(), 
               "destroy_js":instance.get_destroy_js(),
               'init_js':instance.get_init_js(), 
               'type':module_type}

    return content

def render_module(user, request, module, module_object_preload):
    ''' Generic dispatch for internal modules. '''
    if module==None :
        return {"content":""}
    return render_x_module(user, request, module, module_object_preload)
