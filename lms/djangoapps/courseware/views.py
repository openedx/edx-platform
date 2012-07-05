import logging
import urllib

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

from module_render import toc_for_course, get_module, get_section
from models import StudentModuleCache
from student.models import UserProfile
from multicourse import multicourse_settings
from xmodule.modulestore.django import modulestore

from util.cache import cache
from student.models import UserTestGroup
from courseware import grades

log = logging.getLogger("mitx.courseware")

template_imports = {'urllib': urllib}


def user_groups(user):
    if not user.is_authenticated():
        return []

    # TODO: Rewrite in Django
    key = 'user_group_names_{user.id}'.format(user=user)
    cache_expiration = 60 * 60  # one hour

    # Kill caching on dev machines -- we switch groups a lot
    group_names = cache.get(key)

    if group_names is None:
        group_names = [u.name for u in UserTestGroup.objects.filter(users=user)]
        cache.set(key, group_names, cache_expiration)

    return group_names


def format_url_params(params):
    return [urllib.quote(string.replace(' ', '_')) for string in params]


@ensure_csrf_cookie
def courses(request):
  csrf_token = csrf(request)['csrf_token']
  # TODO: Clean up how 'error' is done.
  context = {'courses' : settings.COURSES,
             'csrf' : csrf_token}
  return render_to_response("courses.html", context)

@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def gradebook(request):
    if 'course_admin' not in user_groups(request.user):
        raise Http404

    course = settings.COURSES_BY_ID[course_id]

    student_objects = User.objects.all()[:100]
    student_info = []

    for student in student_objects:
        # TODO (cpennington): do the right thing with courses
        student_module_cache = StudentModuleCache(student, modulestore().get_item(course_location))
        course, _, _, _ = get_module(request.user, request, course_location, student_module_cache)
        student_info.append({
            'username': student.username,
            'id': student.id,
            'email': student.email,
            'grade_info': grades.grade_sheet(student, course, student_module_cache),
            'realname': UserProfile.objects.get(user=student).name
        })

    return render_to_response('gradebook.html', {'students': student_info, 'course': course})


@login_required
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def profile(request, student_id=None):
    ''' User profile. Show username, location, etc, as well as grades .
        We need to allow the user to change some of these settings .'''
    course = settings.COURSES_BY_ID[course_id]
    if student_id is None:
        student = request.user
    else:
        if 'course_admin' not in user_groups(request.user):
            raise Http404
        student = User.objects.get(id=int(student_id))

    user_info = UserProfile.objects.get(user=student)

    # TODO (cpennington): do the right thing with courses
    student_module_cache = StudentModuleCache(request.user, modulestore().get_item(course_location))
    course, _, _, _ = get_module(request.user, request, course_location, student_module_cache)

    context = {'name': user_info.name,
               'username': student.username,
               'location': user_info.location,
               'language': user_info.language,
               'email': student.email,
               'course': course,
               'format_url_params': content_parser.format_url_params,
               'csrf': csrf(request)['csrf_token']
               }
    context.update(grades.grade_sheet(student, course, student_module_cache))

    return render_to_response('profile.html', context)


def render_accordion(request, course, chapter, section):
    ''' Draws navigation bar. Takes current position in accordion as
        parameter.

        If chapter and section are '' or None, renders a default accordion.

        Returns (initialization_javascript, content)'''

    # TODO (cpennington): do the right thing with courses
    toc = toc_for_course(request.user, request, course_location, chapter, section)

    active_chapter = 1
    for i in range(len(toc)):
        if toc[i]['active']:
            active_chapter = i

    context = dict([('active_chapter', active_chapter),
                    ('toc', toc),
                    ('course_name', course.title),
                    ('course_id', course.id),
                    ('format_url_params', format_url_params),
                    ('csrf', csrf(request)['csrf_token'])] + template_imports.items())
    return render_to_string('accordion.html', context)


def get_module_xml(user, course, chapter, section):
    ''' Look up the module xml for the given course/chapter/section path.

    Takes the user to look up the course file.

    Returns None if there was a problem, or the lxml etree for the module.
    '''
    try:
        # this is the course.xml etree
        dom = content_parser.course_file(user, course)
    except:
        log.exception("Unable to parse courseware xml")
        return None

    # this is the module's parent's etree
    path = "//course[@name=$course]/chapter[@name=$chapter]//section[@name=$section]"
    dom_module = dom.xpath(path, course=course.name, chapter=chapter, section=section)

    module_wrapper = dom_module[0] if len(dom_module) > 0 else None
    if module_wrapper is None:
        module = None
    elif module_wrapper.get("src"):
        module = content_parser.section_file(
            user=user, section=module_wrapper.get("src"), coursename=course)
    else:
        # Copy the element out of the module's etree
        module = etree.XML(etree.tostring(module_wrapper[0]))
    return module


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def index(request, course=None, chapter=None, section=None,
          position=None, course_id=None):
    ''' Displays courseware accordion, and any associated content.
    If course, chapter, and section aren't all specified, just returns
    the accordion.  If they are specified, returns an error if they don't
    point to a valid module.

    Arguments:

     - request    : HTTP request
     - course     : coursename (str)
     - chapter    : chapter name (str)
     - section    : section name (str)
     - position   : position in module, eg of <sequential> module (str)

    Returns:

     - HTTPresponse
    '''
    def clean(s):
        ''' Fixes URLs -- we convert spaces to _ in URLs to prevent
        funny encoding characters and keep the URLs readable.  This undoes
        that transformation.
        '''
        return s.replace('_', ' ') if s is not None else None

    if not settings.COURSEWARE_ENABLED:
        return redirect('/')

    chapter = clean(chapter)
    section = clean(section)

    context = {
        'csrf': csrf(request)['csrf_token'],
        'accordion': render_accordion(request, course, chapter, section),
        'COURSE_TITLE': course.title,
        'course': course,
        'init': '',
        'content': ''
    }

    look_for_module = chapter is not None and section is not None
    if look_for_module:
        # TODO (cpennington): Pass the right course in here
        section = get_section(course_location, chapter, section)
        student_module_cache = StudentModuleCache(request.user, section)
        module, _, _, _ = get_module(request.user, request, section.location, student_module_cache)
        context['content'] = module.get_html()

    result = render_to_response('courseware.html', context)
    return result


def jump_to(request, probname=None):
    '''
    Jump to viewing a specific problem.  The problem is specified by a
    problem name - currently the filename (minus .xml) of the problem.
    Maybe this should change to a more generic tag, eg "name" given as
    an attribute in <problem>.

    We do the jump by (1) reading course.xml to find the first
    instance of <problem> with the given filename, then (2) finding
    the parent element of the problem, then (3) rendering that parent
    element with a specific computed position value (if it is
    <sequential>).

    '''
    # get coursename if stored
    coursename = multicourse_settings.get_coursename_from_request(request)

    # begin by getting course.xml tree
    xml = content_parser.course_file(request.user, coursename)

    # look for problem of given name
    pxml = xml.xpath('//problem[@filename="%s"]' % probname)
    if pxml:
        pxml = pxml[0]

    # get the parent element
    parent = pxml.getparent()

    # figure out chapter and section names
    chapter = None
    section = None
    branch = parent
    for k in range(4):  # max depth of recursion
        if branch.tag == 'section':
            section = branch.get('name')
        if branch.tag == 'chapter':
            chapter = branch.get('name')
        branch = branch.getparent()

    position = None
    if parent.tag == 'sequential':
        position = parent.index(pxml) + 1  # position in sequence

    return index(request,
                 course=coursename, chapter=chapter,
                 section=section, position=position)


@ensure_csrf_cookie
def course_info(request, course_id):
    csrf_token = csrf(request)['csrf_token']

    try:
        course = settings.COURSES_BY_ID[course_id]
    except KeyError:
        raise Http404("Course not found")

    return render_to_response('info.html', {'csrf': csrf_token, 'course' : course})
