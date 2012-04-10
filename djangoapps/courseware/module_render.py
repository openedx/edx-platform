import StringIO
import json
import logging
import os
import sys
import sys
import urllib
import uuid

from lxml import etree

from django.conf import settings
from django.contrib.auth.models import User
from django.core.context_processors import csrf
from django.db import connection
from django.http import Http404
from django.http import HttpResponse
from django.shortcuts import redirect
from django.template import Context
from django.template import Context, loader
from mitxmako.shortcuts import render_to_response, render_to_string

from models import StudentModule
from student.models import UserProfile
import track.views

import courseware.content_parser as content_parser

import courseware.modules

log = logging.getLogger("mitx.courseware")

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
    if not request.user.is_authenticated():
        return redirect('/')

    # Grab the student information for the module from the database
    s = StudentModule.objects.filter(student=request.user, 
                                     module_id=id)
    #s = StudentModule.get_with_caching(request.user, id)
    if len(s) == 0 or s is None:
        log.debug("Couldnt find module for user and id " + str(module) + " " + str(request.user) + " "+ str(id))
        raise Http404
    s = s[0]

    oldgrade = s.grade
    oldstate = s.state

    dispatch=dispatch.split('?')[0]

    ajax_url = '/modx/'+module+'/'+id+'/'

    # Grab the XML corresponding to the request from course.xml
    xml = content_parser.module_xml(request.user, module, 'id', id)

    # Create the module
    instance=courseware.modules.get_module_class(module)(xml, 
                                                         id, 
                                                         ajax_url=ajax_url, 
                                                         state=oldstate, 
                                                         track_function = make_track_function(request), 
                                                         render_function = None)
    # Let the module handle the AJAX
    ajax_return=instance.handle_ajax(dispatch, request.POST)
    # Save the state back to the database
    s.state=instance.get_state()
    if instance.get_score(): 
        s.grade=instance.get_score()['score']
    if s.grade != oldgrade or s.state != oldstate:
        s.save()
    # Return whatever the module wanted to return to the client/caller
    return HttpResponse(ajax_return)

def grade_histogram(module_id):
    print module_id
    from django.db import connection, transaction
    cursor = connection.cursor()

    cursor.execute("select courseware_studentmodule.grade,COUNT(courseware_studentmodule.student_id) from courseware_studentmodule where courseware_studentmodule.module_id=%s group by courseware_studentmodule.grade", [module_id])

    grades = list(cursor.fetchall())
    print grades
    grades.sort(key=lambda x:x[0]) # Probably not necessary
    return grades

def render_x_module(user, request, xml_module, module_object_preload):
    ''' Generic module for extensions. This renders to HTML. '''
    # Check if problem has an instance in DB
    module_type=xml_module.tag
    module_class=courseware.modules.get_module_class(module_type)
    module_id=xml_module.get('id') #module_class.id_attribute) or "" 

    # Grab state from database
    smod = object_cache(module_object_preload, 
                        user, 
                        module_type, 
                        module_id)

    if not smod: # If nothing in the database...
        state=None
    else:
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
    if not smod:
        smod=StudentModule(student=user, 
                           module_type = module_type,
                           module_id=module_id, 
                           state=instance.get_state())
        smod.save()
        module_object_preload.append(smod)
    # Grab content
    content = instance.get_html()
    if user.is_staff:
        content=content+render_to_string("staff_problem_info.html", {'xml':etree.tostring(xml_module), 
                                                                     'histogram':grade_histogram(module_id)})
    content = {'content':content, 
               "destroy_js":instance.get_destroy_js(),
               'init_js':instance.get_init_js(), 
               'type':module_type}

    return content

def render_module(user, request, module, module_object_preload):
    ''' Generic dispatch for internal modules. '''
    if module==None :
        return {"content":""}
    return render_x_module(user, request, module, module_object_preload)
