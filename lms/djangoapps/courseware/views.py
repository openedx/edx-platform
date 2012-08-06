from collections import defaultdict
import json
import logging
import urllib
import itertools

from django.conf import settings
from django.core.context_processors import csrf
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse
from django.shortcuts import redirect
from mitxmako.shortcuts import render_to_response, render_to_string
#from django.views.decorators.csrf import ensure_csrf_cookie
from django_future.csrf import ensure_csrf_cookie
from django.views.decorators.cache import cache_control

from module_render import toc_for_course, get_module, get_section
from models import StudentModuleCache
from student.models import UserProfile
from xmodule.modulestore import Location
from xmodule.modulestore.search import path_to_location
from xmodule.modulestore.exceptions import InvalidLocationError, ItemNotFoundError, NoPathToItem
from xmodule.modulestore.django import modulestore
from xmodule.course_module import CourseDescriptor

from util.cache import cache, cache_if_anonymous
from student.models import UserTestGroup, CourseEnrollment
from courseware import grades
from courseware.courses import check_course


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
    if settings.DEBUG:
        group_names = None

    if group_names is None:
        group_names = [u.name for u in UserTestGroup.objects.filter(users=user)]
        cache.set(key, group_names, cache_expiration)

    return group_names



@ensure_csrf_cookie
@cache_if_anonymous
def courses(request):
    # TODO: Clean up how 'error' is done.

    # filter out any courses that errored.
    courses = [c for c in modulestore().get_courses()
               if isinstance(c, CourseDescriptor)]
    courses = sorted(courses, key=lambda course: course.number)
    universities = defaultdict(list)
    for course in courses:
        universities[course.org].append(course)

    return render_to_response("courses.html", {'universities': universities})


@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def gradebook(request, course_id):
    if 'course_admin' not in user_groups(request.user):
        raise Http404
    course = check_course(course_id)
    
    sections, all_descriptors = grades.get_graded_sections(course)
    
    student_objects = User.objects.all()[:100]
    student_info = []
    
    #TODO: Only select students who are in the course
    for student in student_objects:
        student_module_cache = StudentModuleCache(student, descriptors=all_descriptors)
        
        student_info.append({
            'username': student.username,
            'id': student.id,
            'email': student.email,
            'grade_summary': grades.fast_grade(student, request, sections, course.grader, student_module_cache),
            'realname': UserProfile.objects.get(user=student).name
        })

    return render_to_response('gradebook.html', {'students': student_info, 'course': course})


@login_required
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def profile(request, course_id, student_id=None):
    ''' User profile. Show username, location, etc, as well as grades .
        We need to allow the user to change some of these settings .'''
    course = check_course(course_id)

    if student_id is None:
        student = request.user
    else:
        if 'course_admin' not in user_groups(request.user):
            raise Http404
        student = User.objects.get(id=int(student_id))

    user_info = UserProfile.objects.get(user=student)

    student_module_cache = StudentModuleCache(request.user, course)
    course_module = get_module(request.user, request, course.location, student_module_cache)
    
    courseware_summary = grades.grade_sheet(student, course_module, course.grader, student_module_cache)
    sections, _ = grades.get_graded_sections(course)
    grade_summary = grades.fast_grade(request.user, request, sections, course.grader, student_module_cache)
    
    context = {'name': user_info.name,
               'username': student.username,
               'location': user_info.location,
               'language': user_info.language,
               'email': student.email,
               'course': course,
               'csrf': csrf(request)['csrf_token'],
               'courseware_summary' : courseware_summary,
               'grade_summary' : grade_summary
               }
    context.update()

    return render_to_response('profile.html', context)


def render_accordion(request, course, chapter, section):
    ''' Draws navigation bar. Takes current position in accordion as
        parameter.

        If chapter and section are '' or None, renders a default accordion.

        Returns the html string'''

    # grab the table of contents
    toc = toc_for_course(request.user, request, course, chapter, section)

    active_chapter = 1
    for i in range(len(toc)):
        if toc[i]['active']:
            active_chapter = i

    context = dict([('active_chapter', active_chapter),
                    ('toc', toc),
                    ('course_name', course.title),
                    ('course_id', course.id),
                    ('csrf', csrf(request)['csrf_token'])] + template_imports.items())
    return render_to_string('accordion.html', context)


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def index(request, course_id, chapter=None, section=None,
          position=None):
    ''' Displays courseware accordion, and any associated content.
    If course, chapter, and section aren't all specified, just returns
    the accordion.  If they are specified, returns an error if they don't
    point to a valid module.

    Arguments:

     - request    : HTTP request
     - course_id  : course id (str: ORG/course/URL_NAME)
     - chapter    : chapter url_name (str)
     - section    : section url_name (str)
     - position   : position in module, eg of <sequential> module (str)

    Returns:

     - HTTPresponse
    '''
    course = check_course(course_id)
    try:
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
            section_descriptor = get_section(course, chapter, section)
            if section_descriptor is not None:
                student_module_cache = StudentModuleCache(request.user,
                                                          section_descriptor)
                module, _, _, _ = get_module(request.user, request,
                                             section_descriptor.location,
                                             student_module_cache)
                context['content'] = module.get_html()
            else:
                log.warning("Couldn't find a section descriptor for course_id '{0}',"
                            "chapter '{1}', section '{2}'".format(
                                course_id, chapter, section))
        else:
            if request.user.is_staff:
                # Add a list of all the errors...
                context['course_errors'] = modulestore().get_item_errors(course.location)

        result = render_to_response('courseware.html', context)
    except:
        # In production, don't want to let a 500 out for any reason
        if settings.DEBUG:
            raise
        else:
            log.exception("Error in index view: user={user}, course={course},"
                          " chapter={chapter} section={section}"
                          "position={position}".format(
                              user=request.user,
                              course=course,
                              chapter=chapter,
                              section=section,
                              position=position
                              ))
            try:
                result = render_to_response('courseware-error.html', {})
            except:
                result = HttpResponse("There was an unrecoverable error")

    return result


@ensure_csrf_cookie
def jump_to(request, location):
    '''
    Show the page that contains a specific location.

    If the location is invalid, return a 404.

    If the location is valid, but not present in a course, ?

    If the location is valid, but in a course the current user isn't registered for, ?
        TODO -- let the index view deal with it?
    '''
    # Complain if the location isn't valid
    try:
        location = Location(location)
    except InvalidLocationError:
        raise Http404("Invalid location")

    # Complain if there's not data for this location
    try:
        (course_id, chapter, section, position) = path_to_location(modulestore(), location)
    except ItemNotFoundError:
        raise Http404("No data at this location: {0}".format(location))
    except NoPathToItem:
        raise Http404("This location is not in any class: {0}".format(location))

    # Rely on index to do all error handling
    return index(request, course_id, chapter, section, position)

@ensure_csrf_cookie
def course_info(request, course_id):
    '''
    Display the course's info.html, or 404 if there is no such course.

    Assumes the course_id is in a valid format.
    '''
    course = check_course(course_id)

    return render_to_response('info.html', {'course': course})


@ensure_csrf_cookie
@cache_if_anonymous
def course_about(request, course_id):
    def registered_for_course(course, user):
        if user.is_authenticated():
            return CourseEnrollment.objects.filter(user=user, course_id=course.id).exists()
        else:
            return False
    course = check_course(course_id, course_must_be_open=False)
    registered = registered_for_course(course, request.user)
    return render_to_response('portal/course_about.html', {'course': course, 'registered': registered})


@ensure_csrf_cookie
@cache_if_anonymous
def university_profile(request, org_id):
    all_courses = sorted(modulestore().get_courses(), key=lambda course: course.number)
    valid_org_ids = set(c.org for c in all_courses)
    if org_id not in valid_org_ids:
        raise Http404("University Profile not found for {0}".format(org_id))

    # Only grab courses for this org...
    courses = [c for c in all_courses if c.org == org_id]
    context = dict(courses=courses, org_id=org_id)
    template_file = "university_profile/{0}.html".format(org_id).lower()

    return render_to_response(template_file, context)
