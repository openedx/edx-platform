import logging
import urllib

from fs.osfs import OSFS

from django.conf import settings
from django.core.context_processors import csrf
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import redirect
from mitxmako.shortcuts import render_to_response, render_to_string
#from django.views.decorators.csrf import ensure_csrf_cookie
from django_future.csrf import ensure_csrf_cookie
from django.views.decorators.cache import cache_control

from lxml import etree

from module_render import render_x_module, make_track_function, I4xSystem
from models import StudentModule
from student.models import UserProfile
from multicourse import multicourse_settings

import courseware.content_parser as content_parser
import courseware.modules

import courseware.grades as grades

log = logging.getLogger("mitx.courseware")

etree.set_default_parser(etree.XMLParser(dtd_validation=False, load_dtd=False,
                                         remove_comments = True))

template_imports={'urllib':urllib}

@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def gradebook(request):
    if 'course_admin' not in content_parser.user_groups(request.user):
        raise Http404

    coursename = multicourse_settings.get_coursename_from_request(request)

    student_objects = User.objects.all()[:100]
    student_info = [{'username' :s.username,
                     'id' : s.id,
                     'email': s.email,
                     'grade_info' : grades.grade_sheet(s,coursename), 
                     'realname' : UserProfile.objects.get(user = s).name
                     } for s in student_objects]

    return render_to_response('gradebook.html',{'students':student_info})

@login_required
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def profile(request, student_id = None):
    ''' User profile. Show username, location, etc, as well as grades .
        We need to allow the user to change some of these settings .'''

    if student_id is None:
        student = request.user
    else: 
        if 'course_admin' not in content_parser.user_groups(request.user):
            raise Http404
        student = User.objects.get( id = int(student_id))

    user_info = UserProfile.objects.get(user=student) # request.user.profile_cache # 

    coursename = multicourse_settings.get_coursename_from_request(request)

    context={'name':user_info.name,
             'username':student.username,
             'location':user_info.location,
             'language':user_info.language,
             'email':student.email,
             'format_url_params' : content_parser.format_url_params,
             'csrf':csrf(request)['csrf_token']
             }
    context.update(grades.grade_sheet(student,coursename))

    return render_to_response('profile.html', context)

def render_accordion(request,course,chapter,section):
    ''' Draws navigation bar. Takes current position in accordion as
        parameter. Returns (initialization_javascript, content)'''
    if not course:
        course = "6.002 Spring 2012"

    toc=content_parser.toc_from_xml(content_parser.course_file(request.user,course), chapter, section)
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
    return render_to_string('accordion.html',context)

@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def render_section(request, section):
    ''' TODO: Consolidate with index 
    '''
    user = request.user
    if not settings.COURSEWARE_ENABLED:
        return redirect('/')

    coursename = multicourse_settings.get_coursename_from_request(request)

    try:
        dom = content_parser.section_file(user, section, coursename)
    except:
        log.exception("Unable to parse courseware xml")
        return render_to_response('courseware-error.html', {})

    context = {
        'csrf': csrf(request)['csrf_token'],
        'accordion': render_accordion(request, '', '', '')
    }

    module_ids = dom.xpath("//@id")
    
    if user.is_authenticated():
        module_object_preload = list(StudentModule.objects.filter(student=user, 
                                                                  module_id__in=module_ids))
    else:
        module_object_preload = []
    
    try:
        module = render_x_module(user, request, dom, module_object_preload)
    except:
        log.exception("Unable to load module")
        context.update({
            'init': '',
            'content': render_to_string("module-error.html", {}),
        })
        return render_to_response('courseware.html', context)

    context.update({
        'init':module.get('init_js', ''),
        'content':module['content'],
    })

    result = render_to_response('courseware.html', context)
    return result


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def index(request, course=None, chapter="Using the System", section="Hints",position=None): 
    ''' Displays courseware accordion, and any associated content.

    Arguments:

     - request    : HTTP request
     - course     : coursename (str)
     - chapter    : chapter name (str)
     - section    : section name (str)
     - position   : position in module, eg of <sequential> module (str)

    Returns:

     - HTTPresponse

    ''' 
    user = request.user
    if not settings.COURSEWARE_ENABLED:
        return redirect('/')

    if course==None:
        if not settings.ENABLE_MULTICOURSE:
            course = "6.002 Spring 2012"
        elif 'coursename' in request.session:
            course = request.session['coursename']
        else:
            course = settings.COURSE_DEFAULT

    # Fixes URLs -- we don't get funny encoding characters from spaces
    # so they remain readable
    ## TODO: Properly replace underscores
    course=course.replace("_"," ")
    chapter=chapter.replace("_"," ")
    section=section.replace("_"," ")

    # use multicourse module to determine if "course" is valid
    #if course!=settings.COURSE_NAME.replace('_',' '):
    if not multicourse_settings.is_valid_course(course):
        return redirect('/')

    request.session['coursename'] = course		# keep track of current course being viewed in django's request.session

    try:
        # this is the course.xml etree 
        dom = content_parser.course_file(user,course)	# also pass course to it, for course-specific XML path
    except:
        log.exception("Unable to parse courseware xml")
        return render_to_response('courseware-error.html', {})

    # this is the module's parent's etree
    dom_module = dom.xpath("//course[@name=$course]/chapter[@name=$chapter]//section[@name=$section]", 
                           course=course, chapter=chapter, section=section)

    #print "DM", dom_module

    if len(dom_module) == 0:
        module_wrapper = None
    else:
        module_wrapper = dom_module[0]

    if module_wrapper is None:
        module = None
    elif module_wrapper.get("src"):
        module = content_parser.section_file(user=user, section=module_wrapper.get("src"), coursename=course)
    else:
        # this is the module's etree
        module = etree.XML(etree.tostring(module_wrapper[0])) # Copy the element out of the tree

    module_ids = []
    if module is not None:
        module_ids = module.xpath("//@id", 
                                  course=course, chapter=chapter, section=section)

    if user.is_authenticated():
        module_object_preload = list(StudentModule.objects.filter(student=user, 
                                                                  module_id__in=module_ids))
    else:
        module_object_preload = []

    context = {
        'csrf': csrf(request)['csrf_token'],
        'accordion': render_accordion(request, course, chapter, section),
        'COURSE_TITLE':multicourse_settings.get_course_title(course),
    }

    try:
        module_context = render_x_module(user, request, module, module_object_preload, position)
    except:
        log.exception("Unable to load module")
        context.update({
            'init': '',
            'content': render_to_string("module-error.html", {}),
        })
        return render_to_response('courseware.html', context)

    context.update({
        'init': module_context.get('init_js', ''),
        'content': module_context['content'],
    })

    result = render_to_response('courseware.html', context)
    return result

def jump_to(request, probname=None):
    '''
    Jump to viewing a specific problem.  The problem is specified by a problem name - currently the filename (minus .xml)
    of the problem.  Maybe this should change to a more generic tag, eg "name" given as an attribute in <problem>.

    We do the jump by (1) reading course.xml to find the first instance of <problem> with the given filename, then
    (2) finding the parent element of the problem, then (3) rendering that parent element with a specific computed position
    value (if it is <sequential>).

    '''
    # get coursename if stored
    coursename = multicourse_settings.get_coursename_from_request(request)

    # begin by getting course.xml tree
    xml = content_parser.course_file(request.user,coursename)

    # look for problem of given name
    pxml = xml.xpath('//problem[@filename="%s"]' % probname)
    if pxml: pxml = pxml[0]

    # get the parent element
    parent = pxml.getparent()

    # figure out chapter and section names
    chapter = None
    section = None
    branch = parent
    for k in range(4):	# max depth of recursion
        if branch.tag=='section': section = branch.get('name')
        if branch.tag=='chapter': chapter = branch.get('name')
        branch = branch.getparent()

    position = None
    if parent.tag=='sequential':
        position = parent.index(pxml)+1	# position in sequence
        
    return index(request,course=coursename,chapter=chapter,section=section,position=position)

