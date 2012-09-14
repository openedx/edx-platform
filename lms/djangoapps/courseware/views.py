import csv
import json
import logging
import urllib
import itertools
import StringIO

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
from module_render import toc_for_course, get_module, get_instance_module
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


def render_accordion(request, course, chapter, section):
    ''' Draws navigation bar. Takes current position in accordion as
        parameter.

        If chapter and section are '' or None, renders a default accordion.

        course, chapter, and section are the url_names.

        Returns the html string'''

    # grab the table of contents
    toc = toc_for_course(request.user, request, course, chapter, section)

    context = dict([('toc', toc),
                    ('course_id', course.id),
                    ('csrf', csrf(request)['csrf_token'])] + template_imports.items())
    return render_to_string('accordion.html', context)


def get_current_child(xmodule):
    """
    Get the xmodule.position's display item of an xmodule that has a position and
    children.  Returns None if the xmodule doesn't have a position, or if there
    are no children.  Otherwise, if position is out of bounds, returns the first child.
    """
    if not hasattr(xmodule, 'position'):
        return None

    children = xmodule.get_display_items()
    # position is 1-indexed.
    if 0 <= xmodule.position - 1 < len(children):
        child = children[xmodule.position - 1]
    elif len(children) > 0:
        # Something is wrong.  Default to first child
        child = children[0]
    else:
        child = None
    return child


def redirect_to_course_position(course_module, first_time):
    """
    Load the course state for the user, and return a redirect to the
    appropriate place in the course: either the first element if there
    is no state, or their previous place if there is.

    If this is the user's first time, send them to the first section instead.
    """
    course_id = course_module.descriptor.id
    chapter = get_current_child(course_module)
    if chapter is None:
        # oops.  Something bad has happened.
        raise Http404
    if not first_time:
        return redirect(reverse('courseware_chapter', kwargs={'course_id': course_id,
                                                              'chapter': chapter.url_name}))
    # Relying on default of returning first child
    section = get_current_child(chapter)
    return redirect(reverse('courseware_section', kwargs={'course_id': course_id,
                                                          'chapter': chapter.url_name,
                                                          'section': section.url_name}))

def save_child_position(seq_module, child_name, instance_module):
    """
    child_name: url_name of the child
    instance_module: the StudentModule object for the seq_module
    """
    for i, c in enumerate(seq_module.get_display_items()):
        if c.url_name == child_name:
            # Position is 1-indexed
            position = i + 1
            # Only save if position changed
            if position != seq_module.position:
                seq_module.position = position
                instance_module.state = seq_module.get_instance_state()
                instance_module.save()

@login_required
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def index(request, course_id, chapter=None, section=None,
          position=None):
    """
    Displays courseware accordion and associated content.  If course, chapter,
    and section are all specified, renders the page, or returns an error if they
    are invalid.

    If section is not specified, displays the accordion opened to the right chapter.

    If neither chapter or section are specified, redirects to user's most recent
    chapter, or the first chapter if this is the user's first visit.

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
        student_module_cache = StudentModuleCache.cache_for_descriptor_descendents(
            course.id, request.user, course, depth=2)

        # Has this student been in this course before?
        first_time = student_module_cache.lookup(course_id, 'course', course.location.url()) is None

        course_module = get_module(request.user, request, course.location, student_module_cache, course.id)
        if course_module is None:
            log.warning('If you see this, something went wrong: if we got this'
                        ' far, should have gotten a course module for this user')
            return redirect(reverse('about_course', args=[course.id]))

        if chapter is None:
            return redirect_to_course_position(course_module, first_time)

        context = {
            'csrf': csrf(request)['csrf_token'],
            'accordion': render_accordion(request, course, chapter, section),
            'COURSE_TITLE': course.title,
            'course': course,
            'init': '',
            'content': '',
            'staff_access': staff_access,
            }

        chapter_descriptor = course.get_child_by_url_name(chapter)
        if chapter_descriptor is not None:
            instance_module = get_instance_module(course_id, request.user, course_module, student_module_cache)
            save_child_position(course_module, chapter, instance_module)
        else:
            raise Http404

        chapter_module = get_module(request.user, request, chapter_descriptor.location,
                                    student_module_cache, course_id)
        if chapter_module is None:
            # User may be trying to access a chapter that isn't live yet
            raise Http404

        if section is not None:
            section_descriptor = chapter_descriptor.get_child_by_url_name(section)
            if section_descriptor is None:
                # Specifically asked-for section doesn't exist
                raise Http404

            section_student_module_cache = StudentModuleCache.cache_for_descriptor_descendents(
                course_id, request.user, section_descriptor)
            section_module = get_module(request.user, request,
                                section_descriptor.location,
                                section_student_module_cache, course_id, position)
            if section_module is None:
                # User may be trying to be clever and access something
                # they don't have access to.
                raise Http404

            # Save where we are in the chapter
            instance_module = get_instance_module(course_id, request.user, chapter_module, student_module_cache)
            save_child_position(chapter_module, section, instance_module)


            context['content'] = section_module.get_html()
        else:
            # section is none, so display a message
            prev_section = get_current_child(chapter_module)
            if prev_section is None:
                # Something went wrong -- perhaps this chapter has no sections visible to the user
                raise Http404
            prev_section_url = reverse('courseware_section', kwargs={'course_id': course_id,
                                                                     'chapter': chapter_descriptor.url_name,
                                                                     'section': prev_section.url_name})
            context['content'] = render_to_string('courseware/welcome-back.html',
                                                  {'course': course,
                                                   'chapter_module': chapter_module,
                                                   'prev_section': prev_section,
                                                   'prev_section_url': prev_section_url})

        result = render_to_response('courseware/courseware.html', context)
    except Exception as e:
        if isinstance(e, Http404):
            # let it propagate
            raise

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

    if request.REQUEST.get('next', False):
        context['show_login_immediately'] = True

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

