import json
import logging
import urllib
import itertools

from functools import partial

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

from courseware import grades
from courseware.access import has_access
from courseware.courses import (get_course_with_access, get_courses_by_university)
from models import StudentModuleCache
from module_render import toc_for_course, get_module, get_section
from student.models import UserProfile

from multicourse import multicourse_settings

from django_comment_client.utils import get_discussion_title

from student.models import UserTestGroup, CourseEnrollment
from util.cache import cache, cache_if_anonymous
from xmodule.course_module import CourseDescriptor
from xmodule.modulestore import Location
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import InvalidLocationError, ItemNotFoundError, NoPathToItem
from xmodule.modulestore.search import path_to_location

import comment_client




log = logging.getLogger("mitx.courseware")

template_imports = {'urllib': urllib}


def user_groups(user):
    """
    TODO (vshnayder): This is not used. When we have a new plan for groups, adjust appropriately.
    """
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
    '''
    Render "find courses" page.  The course selection work is done in courseware.courses.
    '''
    universities = get_courses_by_university(request.user,
                                             domain=request.META.get('HTTP_HOST'))
    return render_to_response("courses.html", {'universities': universities})


def render_accordion(request, course, chapter, section, course_id=None):
    ''' Draws navigation bar. Takes current position in accordion as
        parameter.

        If chapter and section are '' or None, renders a default accordion.

        course, chapter, and section are the url_names.

        Returns the html string'''

    # grab the table of contents
    toc = toc_for_course(request.user, request, course, chapter, section, course_id=course_id)

    context = dict([('toc', toc),
                    ('course_id', course.id),
                    ('csrf', csrf(request)['csrf_token'])] + template_imports.items())
    return render_to_string('accordion.html', context)


@login_required
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def index(request, course_id, chapter=None, section=None,
          position=None):
    """
    Displays courseware accordion, and any associated content.
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
    """
    course = get_course_with_access(request.user, course_id, 'load')
    staff_access = has_access(request.user, course, 'staff')
    registered = registered_for_course(course, request.user)
    if not registered:
        # TODO (vshnayder): do course instructors need to be registered to see course?
        log.debug('User %s tried to view course %s but is not enrolled' % (request.user,course.location.url()))
        return redirect(reverse('about_course', args=[course.id]))

    try:
        context = {
            'csrf': csrf(request)['csrf_token'],
            'accordion': render_accordion(request, course, chapter, section, course_id=course_id),
            'COURSE_TITLE': course.title,
            'course': course,
            'init': '',
            'content': '',
            'staff_access': staff_access,
            }

        look_for_module = chapter is not None and section is not None
        if look_for_module:
            section_descriptor = get_section(course, chapter, section)
            if section_descriptor is not None:
                student_module_cache = StudentModuleCache.cache_for_descriptor_descendents(
                    course_id, request.user, section_descriptor)
                module = get_module(request.user, request,
                                    section_descriptor.location,
                                    student_module_cache, course_id, position)
                if module is None:
                    # User is probably being clever and trying to access something
                    # they don't have access to.
                    raise Http404
                context['content'] = module.get_html()
            else:
                log.warning("Couldn't find a section descriptor for course_id '{0}',"
                            "chapter '{1}', section '{2}'".format(
                                course_id, chapter, section))
        else:
            if request.user.is_staff:
                # Add a list of all the errors...
                context['course_errors'] = modulestore().get_item_errors(course.location)

        result = render_to_response('courseware/courseware.html', context)
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
                result = render_to_response('courseware/courseware-error.html',
                                            {'staff_access': staff_access,
                                            'course' : course})
            except:
                # Let the exception propagate, relying on global config to at
                # at least return a nice error message
                log.exception("Error while rendering courseware-error page")
                raise

    return result


@ensure_csrf_cookie
def jump_to(request, course_id, location):
    '''
    Show the page that contains a specific location.

    If the location is invalid or not in any class, return a 404.

    Otherwise, delegates to the index view to figure out whether this user
    has access, and what they should see.
    '''
    # Complain if the location isn't valid
    try:
        location = Location(location)
    except InvalidLocationError:
        raise Http404("Invalid location")

    # Complain if there's not data for this location
    try:
        (course_id, chapter, section, position) = path_to_location(modulestore(), course_id, location)
    except ItemNotFoundError:
        raise Http404("No data at this location: {0}".format(location))
    except NoPathToItem:
        raise Http404("This location is not in any class: {0}".format(location))

    # Rely on index to do all error handling and access control.
    return redirect('courseware_position',
                    course_id=course_id, 
                    chapter=chapter, 
                    section=section, 
                    position=position)
@ensure_csrf_cookie
def course_info(request, course_id):
    """
    Display the course's info.html, or 404 if there is no such course.

    Assumes the course_id is in a valid format.
    """
    course = get_course_with_access(request.user, course_id, 'load')
    staff_access = has_access(request.user, course, 'staff')

    return render_to_response('courseware/info.html', {'course': course,
                                            'staff_access': staff_access,})

# TODO arjun: remove when custom tabs in place, see courseware/syllabus.py
@ensure_csrf_cookie
def syllabus(request, course_id):
    """
    Display the course's syllabus.html, or 404 if there is no such course.

    Assumes the course_id is in a valid format.
    """
    course = get_course_with_access(request.user, course_id, 'load')
    staff_access = has_access(request.user, course, 'staff')

    return render_to_response('courseware/syllabus.html', {'course': course,
                                            'staff_access': staff_access,})

def registered_for_course(course, user):
    '''Return CourseEnrollment if user is registered for course, else False'''
    if user is None:
        return False
    if user.is_authenticated():
        return CourseEnrollment.objects.filter(user=user, course_id=course.id).exists()
    else:
        return False

@ensure_csrf_cookie
@cache_if_anonymous
def course_about(request, course_id):
    course = get_course_with_access(request.user, course_id, 'see_exists')
    registered = registered_for_course(course, request.user)

    if has_access(request.user, course, 'load'):
        course_target = reverse('info', args=[course.id])
    else:
        course_target = reverse('about_course', args=[course.id])

    show_courseware_link = (has_access(request.user, course, 'load') or
                            settings.MITX_FEATURES.get('ENABLE_LMS_MIGRATION'))

    return render_to_response('portal/course_about.html',
                              {'course': course,
                               'registered': registered,
                               'course_target': course_target,
                               'show_courseware_link' : show_courseware_link})


@ensure_csrf_cookie
@cache_if_anonymous
def university_profile(request, org_id):
    """
    Return the profile for the particular org_id.  404 if it's not valid.
    """
    all_courses = modulestore().get_courses()
    valid_org_ids = set(c.org for c in all_courses)
    if org_id not in valid_org_ids:
        raise Http404("University Profile not found for {0}".format(org_id))

    # Only grab courses for this org...
    courses = get_courses_by_university(request.user,
                                        domain=request.META.get('HTTP_HOST'))[org_id]
    context = dict(courses=courses, org_id=org_id)
    template_file = "university_profile/{0}.html".format(org_id).lower()

    return render_to_response(template_file, context)

def render_notifications(request, course, notifications):
    context = {
        'notifications': notifications,
        'get_discussion_title': partial(get_discussion_title, request=request, course=course),
        'course': course,
    }
    return render_to_string('notifications.html', context)

@login_required
def news(request, course_id):
    course = get_course_with_access(request.user, course_id, 'load')

    notifications = comment_client.get_notifications(request.user.id)

    context = {
        'course': course,
        'content': render_notifications(request, course, notifications),
    }

    return render_to_response('news.html', context)

@login_required
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def progress(request, course_id, student_id=None):
    """ User progress. We show the grade bar and every problem score.

    Course staff are allowed to see the progress of students in their class.
    """
    course = get_course_with_access(request.user, course_id, 'load')
    staff_access = has_access(request.user, course, 'staff')

    if student_id is None or student_id == request.user.id:
        # always allowed to see your own profile
        student = request.user
    else:
        # Requesting access to a different student's profile
        if not staff_access:
            raise Http404
        student = User.objects.get(id=int(student_id))

    # NOTE: To make sure impersonation by instructor works, use
    # student instead of request.user in the rest of the function.

    # The pre-fetching of groups is done to make auth checks not require an 
    # additional DB lookup (this kills the Progress page in particular).
    student = User.objects.prefetch_related("groups").get(id=student.id)

    student_module_cache = StudentModuleCache.cache_for_descriptor_descendents(
        course_id, student, course)
    course_module = get_module(student, request, course.location,
                               student_module_cache, course_id)

    # The course_module should be accessible, but check anyway just in case something went wrong:
    if course_module is None:
        raise Http404("Course does not exist")

    courseware_summary = grades.progress_summary(student, course_module,
                                                 course.grader, student_module_cache)
    grade_summary = grades.grade(student, request, course, student_module_cache)

    context = {'course': course,
               'courseware_summary': courseware_summary,
               'grade_summary': grade_summary,
               'staff_access': staff_access,
               }
    context.update()

    return render_to_response('courseware/progress.html', context)



