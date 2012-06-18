import json
import logging

from lxml import etree

from django.http import Http404
from django.http import HttpResponse
from django.shortcuts import redirect

from fs.osfs import OSFS

from django.conf import settings
from mitxmako.shortcuts import render_to_string, render_to_response

from models import StudentModule
from multicourse import multicourse_settings
from util.views import accepts

import courseware.content_parser as content_parser
import xmodule

log = logging.getLogger("mitx.courseware")

class I4xSystem(object):
    '''
    This is an abstraction such that x_modules can function independent 
    of the courseware (e.g. import into other types of courseware, LMS, 
    or if we want to have a sandbox server for user-contributed content)

    I4xSystem objects are passed to x_modules to provide access to system
    functionality.

    Note that these functions can be closures over e.g. a django request
    and user, or other environment-specific info.
    '''
    def __init__(self, ajax_url, track_function, render_function,
                 render_template, filestore=None):
        '''
        Create a closure around the system environment.

        ajax_url - the url where ajax calls to the encapsulating module go.
        track_function - function of (event_type, event), intended for logging
                         or otherwise tracking the event.
                         TODO: Not used, and has inconsistent args in different
                         files.  Update or remove.
        render_function - function that takes (module_xml) and renders it,
                          returning a dictionary with a context for rendering the
                          module to html.  Dictionary will contain keys 'content'
                          and 'type'.
        render_template - a function that takes (template_file, context), and returns
                          rendered html.
        filestore - A filestore ojbect.  Defaults to an instance of OSFS based at
                    settings.DATA_DIR.
        '''
        self.ajax_url = ajax_url
        self.track_function = track_function
        if not filestore: 
            self.filestore = OSFS(settings.DATA_DIR)
        else:
            self.filestore = filestore
            if settings.DEBUG:
                log.info("[courseware.module_render.I4xSystem] filestore path = %s",
                         filestore)
        self.render_function = render_function
        self.render_template = render_template
        self.exception404 = Http404
        self.DEBUG = settings.DEBUG

    def get(self, attr):
        '''	provide uniform access to attributes (like etree).'''
        return self.__dict__.get(attr)
    
    def set(self,attr,val):
        '''provide uniform access to attributes (like etree)'''
        self.__dict__[attr] = val

    def __repr__(self):
        return repr(self.__dict__)

    def __str__(self):
        return str(self.__dict__)

def smod_cache_lookup(cache, module_type, module_id):
    '''
    Look for a student module with the given type and id in the cache.

    cache -- list of student modules

    returns first found object, or None
    '''
    for o in cache: 
        if o.module_type == module_type and o.module_id == module_id:
            return o
    return None

def make_track_function(request):
    ''' 
    Make a tracking function that logs what happened.
    For use in I4xSystem.
    '''
    import track.views

    def f(event_type, event):
        return track.views.server_track(request, event_type, event, page='x_module')
    return f

def grade_histogram(module_id):
    ''' Print out a histogram of grades on a given problem. 
        Part of staff member debug info.
    '''
    from django.db import connection
    cursor = connection.cursor()

    q = """SELECT courseware_studentmodule.grade,
                  COUNT(courseware_studentmodule.student_id)
    FROM courseware_studentmodule
    WHERE courseware_studentmodule.module_id=%s
    GROUP BY courseware_studentmodule.grade"""
    # Passing module_id this way prevents sql-injection.
    cursor.execute(q, [module_id])

    grades = list(cursor.fetchall())
    grades.sort(key=lambda x: x[0])          # Add ORDER BY to sql query?
    if len(grades) == 1 and grades[0][0] is None:
        return []
    return grades

def get_module(user, request, module_xml, student_module_cache, position=None):
    ''' Get an instance of the xmodule class corresponding to module_xml,
    setting the state based on an existing StudentModule, or creating one if none
    exists.

    Arguments:
      - user                  : current django User
      - request               : current django HTTPrequest
      - module_xml            : lxml etree of xml subtree for the requested module
      - student_module_cache  : list of StudentModule objects, one of which may
                                match this module type and id
      - position   	          : extra information from URL for user-specified
                                position within module

    Returns:
      - a tuple (xmodule instance, student module, module type).
    '''
    module_type = module_xml.tag
    module_class = xmodule.get_module_class(module_type)
    module_id = module_xml.get('id')

    # Grab xmodule state from StudentModule cache
    smod = smod_cache_lookup(student_module_cache, module_type, module_id)
    state = smod.state if smod else None

    # get coursename if present in request
    coursename = multicourse_settings.get_coursename_from_request(request)

    if coursename and settings.ENABLE_MULTICOURSE:
        # path to XML for the course
        xp = multicourse_settings.get_course_xmlpath(coursename)
        data_root = settings.DATA_DIR + xp
    else:
        data_root = settings.DATA_DIR

    # Setup system context for module instance
    ajax_url = settings.MITX_ROOT_URL + '/modx/' + module_type + '/' + module_id + '/'

    system = I4xSystem(track_function = make_track_function(request), 
                       render_function = lambda xml: render_x_module(
                           user, request, xml, student_module_cache, position),
                       render_template = render_to_string,
                       ajax_url = ajax_url,
                       filestore = OSFS(data_root),
                       )
    # pass position specified in URL to module through I4xSystem
    system.set('position', position) 
    instance = module_class(system, 
                            etree.tostring(module_xml), 
                            module_id, 
                            state=state)
    
    # If StudentModule for this instance wasn't already in the database,
    # and this isn't a guest user, create it.
    if not smod and user.is_authenticated():
        smod = StudentModule(student=user, module_type = module_type,
                           module_id=module_id, state=instance.get_state())
        smod.save()
        # Add to cache. The caller and the system context have references
        # to it, so the change persists past the return
        student_module_cache.append(smod)

    return (instance, smod, module_type)

def render_x_module(user, request, module_xml, student_module_cache, position=None):
    ''' Generic module for extensions. This renders to HTML.

    modules include sequential, vertical, problem, video, html

    Note that modules can recurse.  problems, video, html, can be inside sequential or vertical.

    Arguments:

      - user                  : current django User
      - request               : current django HTTPrequest
      - module_xml            : lxml etree of xml subtree for the current module
      - student_module_cache : list of StudentModule objects, one of which may match this module type and id
      - position   	      : extra information from URL for user-specified position within module

    Returns:

      - dict which is context for HTML rendering of the specified module.  Will have
      key 'content', and will have 'type' key if passed a valid module.
    '''
    if module_xml is None :
        return {"content": ""}

    (instance, smod, module_type) = get_module(
        user, request, module_xml, student_module_cache, position)

    content = instance.get_html()

    # special extra information about each problem, only for users who are staff 
    if settings.MITX_FEATURES.get('DISPLAY_HISTOGRAMS_TO_STAFF') and user.is_staff:
        module_id = module_xml.get('id')
        histogram = grade_histogram(module_id)
        render_histogram = len(histogram) > 0
        staff_context = {'xml': etree.tostring(module_xml), 
                         'module_id': module_id,
                         'histogram': json.dumps(histogram),
                         'render_histogram': render_histogram}
        content += render_to_string("staff_problem_info.html", staff_context)

    context = {'content': content, 'type': module_type}
    return context

def modx_dispatch(request, module=None, dispatch=None, id=None):
    ''' Generic view for extensions. This is where AJAX calls go.

    Arguments:

      - request -- the django request.
      - module -- the type of the module, as used in the course configuration xml.
                  e.g. 'problem', 'video', etc
      - dispatch -- the command string to pass through to the module's handle_ajax call
           (e.g. 'problem_reset').  If this string contains '?', only pass
           through the part before the first '?'.
      - id -- the module id.  Used to look up the student module.
            e.g. filenamexformularesponse
    '''
    # ''' (fix emacs broken parsing)
    if not request.user.is_authenticated():
        return redirect('/')

    # python concats adjacent strings
    error_msg = ("We're sorry, this module is temporarily unavailable. "
                 "Our staff is working to fix it as soon as possible")


    # Grab the student information for the module from the database
    s = StudentModule.objects.filter(student=request.user, 
                                     module_id=id)

    if s is None or len(s) == 0:
        log.debug("Couldn't find module '%s' for user '%s' and id '%s'",
                  module, request.user, id)
        raise Http404
    s = s[0]

    oldgrade = s.grade
    oldstate = s.state

    # If there are arguments, get rid of them
    dispatch, _, _ = dispatch.partition('?')

    ajax_url = '{root}/modx/{module}/{id}'.format(root = settings.MITX_ROOT_URL,
                                                  module=module, id=id)
    coursename = multicourse_settings.get_coursename_from_request(request)
    if coursename and settings.ENABLE_MULTICOURSE:
        xp = multicourse_settings.get_course_xmlpath(coursename)
        data_root = settings.DATA_DIR + xp
    else:
        data_root = settings.DATA_DIR

    # Grab the XML corresponding to the request from course.xml
    try:
        xml = content_parser.module_xml(request.user, module, 'id', id, coursename)
    except:
        log.exception(
            "Unable to load module during ajax call. module=%s, dispatch=%s, id=%s",
            module, dispatch, id)
        if accepts(request, 'text/html'):
            return render_to_response("module-error.html", {})
        else:
            response = HttpResponse(json.dumps({'success': error_msg}))
        return response

    # Create the module
    system = I4xSystem(track_function = make_track_function(request), 
                       render_function = None, 
                       render_template = render_to_string,
                       ajax_url = ajax_url,
                       filestore = OSFS(data_root),
                       )

    try:
        module_class = xmodule.get_module_class(module)
        instance = module_class(system, xml, id, state=oldstate)
    except:
        log.exception("Unable to load module instance during ajax call")
        if accepts(request, 'text/html'):
            return render_to_response("module-error.html", {})
        else:
            response = HttpResponse(json.dumps({'success': error_msg}))
        return response

    # Let the module handle the AJAX
    ajax_return = instance.handle_ajax(dispatch, request.POST)

    # Save the state back to the database
    s.state = instance.get_state()
    if instance.get_score(): 
        s.grade = instance.get_score()['score']
    if s.grade != oldgrade or s.state != oldstate:
        s.save()
    # Return whatever the module wanted to return to the client/caller
    return HttpResponse(ajax_return)
