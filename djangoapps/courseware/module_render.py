import logging

from lxml import etree

from django.http import Http404
from django import settings
from mitxmako.shortcuts import render_to_string
from fs.osfs import OSFS


from models import StudentModule
import track.views

import courseware.modules

log = logging.getLogger("mitx.courseware")

class I4xSystem(object):
    def __init__(self, ajax_url, track_function, render_function, filestore=None):
        self.ajax_url = ajax_url
        self.track_function = track_function
        self.filestore = OSFS(settings.DATA_DIR)
        self.render_function = render_function
        self.exception404 = Http404

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
    ''' We want the capa problem (and other modules) to be able to
    track/log what happens inside them without adding dependencies on
    Django or the rest of the codebase. We do this by passing a
    tracking function to them. This generates a closure for each request 
    that gives a clean interface on both sides. 
    '''
    def f(event_type, event):
        return track.views.server_track(request, event_type, event, page='x_module')
    return f

def grade_histogram(module_id):
    ''' Print out a histogram of grades on a given problem. 
        Part of staff member debug info. 
    '''
    from django.db import connection
    cursor = connection.cursor()

    cursor.execute("select courseware_studentmodule.grade,COUNT(courseware_studentmodule.student_id) from courseware_studentmodule where courseware_studentmodule.module_id=%s group by courseware_studentmodule.grade", [module_id])

    grades = list(cursor.fetchall())
    grades.sort(key=lambda x:x[0]) # Probably not necessary
    if (len(grades) == 1 and grades[0][0] == None):
        return []
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
    system = I4xSystem(track_function = make_track_function(request), 
                       render_function = lambda x: render_module(user, request, x, module_object_preload), 
                       ajax_url = ajax_url,
                       filestore = None
                       )
    instance=module_class(system, 
                          etree.tostring(xml_module), 
                          module_id, 
                          state=state)
    
    # If instance wasn't already in the database, and this
    # isn't a guest user, create it
    if not smod and user.is_authenticated():
        smod=StudentModule(student=user, 
                           module_type = module_type,
                           module_id=module_id, 
                           state=instance.get_state())
        smod.save()
        module_object_preload.append(smod)
    # Grab content
    content = instance.get_html()
    init_js = instance.get_init_js()
    destory_js = instance.get_destroy_js()
    if user.is_staff:
        histogram = grade_histogram(module_id)
        render_histogram = len(histogram) > 0
        content=content+render_to_string("staff_problem_info.html", {'xml':etree.tostring(xml_module), 
                                                                     'module_id' : module_id,
                                                                     'render_histogram' : render_histogram})
        if render_histogram:
            init_js = init_js+render_to_string("staff_problem_histogram.js", {'histogram' : histogram,
                                                                              'module_id' : module_id})
        
    content = {'content':content, 
               "destroy_js":destory_js,
               'init_js':init_js, 
               'type':module_type}

    return content

def render_module(user, request, module, module_object_preload):
    ''' Generic dispatch for internal modules. '''
    if module==None :
        return {"content":""}
    return render_x_module(user, request, module, module_object_preload)
