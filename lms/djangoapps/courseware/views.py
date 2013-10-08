import logging
import urllib

from functools import partial

from django.conf import settings
from django.core.context_processors import csrf
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from mitxmako.shortcuts import render_to_response, render_to_string
from django_future.csrf import ensure_csrf_cookie
from django.views.decorators.cache import cache_control
from markupsafe import escape

from courseware import grades
from courseware.access import has_access
from courseware.courses import (get_courses, get_course_with_access,
                                get_courses_by_university, sort_by_announcement)
import courseware.tabs as tabs
from courseware.masquerade import setup_masquerade
from courseware.model_data import FieldDataCache
from .module_render import toc_for_course, get_module_for_descriptor, get_module
from courseware.models import StudentModule, StudentModuleHistory
from course_modes.models import CourseMode

from django_comment_client.utils import get_discussion_title

from student.models import UserTestGroup, CourseEnrollment
from util.cache import cache, cache_if_anonymous
from xmodule.modulestore import Location
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import InvalidLocationError, ItemNotFoundError, NoPathToItem
from xmodule.modulestore.search import path_to_location
from xmodule.course_module import CourseDescriptor
import shoppingcart

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
    """
    Render "find courses" page.  The course selection work is done in courseware.courses.
    """
    courses = get_courses(request.user, request.META.get('HTTP_HOST'))
    courses = sort_by_announcement(courses)

    return render_to_response("courseware/courses.html", {'courses': courses})


def render_accordion(request, course, chapter, section, field_data_cache):
    """
    Draws navigation bar. Takes current position in accordion as
    parameter.

    If chapter and section are '' or None, renders a default accordion.

    course, chapter, and section are the url_names.

    Returns the html string
    """

    # grab the table of contents
    user = User.objects.prefetch_related("groups").get(id=request.user.id)
    request.user = user	# keep just one instance of User
    toc = toc_for_course(user, request, course, chapter, section, field_data_cache)

    context = dict([('toc', toc),
                    ('course_id', course.id),
                    ('csrf', csrf(request)['csrf_token']),
                    ('due_date_display_format', course.due_date_display_format)] + template_imports.items())
    return render_to_string('courseware/accordion.html', context)


def get_current_child(xmodule):
    """
    Get the xmodule.position's display item of an xmodule that has a position and
    children.  If xmodule has no position or is out of bounds, return the first child.
    Returns None only if there are no children at all.
    """
    if not hasattr(xmodule, 'position'):
        return None

    if xmodule.position is None:
        pos = 0
    else:
        # position is 1-indexed.
        pos = xmodule.position - 1

    children = xmodule.get_display_items()
    if 0 <= pos < len(children):
        child = children[pos]
    elif len(children) > 0:
        # Something is wrong.  Default to first child
        child = children[0]
    else:
        child = None
    return child


def redirect_to_course_position(course_module):
    """
    Return a redirect to the user's current place in the course.

    If this is the user's first time, redirects to COURSE/CHAPTER/SECTION.
    If this isn't the users's first time, redirects to COURSE/CHAPTER,
    and the view will find the current section and display a message
    about reusing the stored position.

    If there is no current position in the course or chapter, then selects
    the first child.

    """
    urlargs = {'course_id': course_module.descriptor.id}
    chapter = get_current_child(course_module)
    if chapter is None:
        # oops.  Something bad has happened.
        raise Http404("No chapter found when loading current position in course")

    urlargs['chapter'] = chapter.url_name
    if course_module.position is not None:
        return redirect(reverse('courseware_chapter', kwargs=urlargs))

    # Relying on default of returning first child
    section = get_current_child(chapter)
    if section is None:
        raise Http404("No section found when loading current position in course")

    urlargs['section'] = section.url_name
    return redirect(reverse('courseware_section', kwargs=urlargs))


def save_child_position(seq_module, child_name):
    """
    child_name: url_name of the child
    """
    for position, c in enumerate(seq_module.get_display_items(), start=1):
        if c.url_name == child_name:
            # Only save if position changed
            if position != seq_module.position:
                seq_module.position = position
    # Save this new position to the underlying KeyValueStore
    seq_module.save()


def check_for_active_timelimit_module(request, course_id, course):
    """
    Looks for a timing module for the given user and course that is currently active.
    If found, returns a context dict with timer-related values to enable display of time remaining.
    """
    context = {}

    # TODO (cpennington): Once we can query the course structure, replace this with such a query
    timelimit_student_modules = StudentModule.objects.filter(student=request.user, course_id=course_id, module_type='timelimit')
    if timelimit_student_modules:
        for timelimit_student_module in timelimit_student_modules:
            # get the corresponding section_descriptor for the given StudentModel entry:
            module_state_key = timelimit_student_module.module_state_key
            timelimit_descriptor = modulestore().get_instance(course_id, Location(module_state_key))
            timelimit_module_cache = FieldDataCache.cache_for_descriptor_descendents(course.id, request.user,
                                                                                     timelimit_descriptor, depth=None)
            timelimit_module = get_module_for_descriptor(request.user, request, timelimit_descriptor,
                                                         timelimit_module_cache, course.id, position=None)
            if timelimit_module is not None and timelimit_module.category == 'timelimit' and \
                    timelimit_module.has_begun and not timelimit_module.has_ended:
                location = timelimit_module.location
                # determine where to go when the timer expires:
                if timelimit_descriptor.time_expired_redirect_url is None:
                    raise Http404("no time_expired_redirect_url specified at this location: {} ".format(timelimit_module.location))
                context['time_expired_redirect_url'] = timelimit_descriptor.time_expired_redirect_url
                # Fetch the remaining time relative to the end time as stored in the module when it was started.
                # This value should be in milliseconds.
                remaining_time = timelimit_module.get_remaining_time_in_ms()
                context['timer_expiration_duration'] = remaining_time
                context['suppress_toplevel_navigation'] = timelimit_descriptor.suppress_toplevel_navigation
                return_url = reverse('jump_to', kwargs={'course_id': course_id, 'location': location})
                context['timer_navigation_return_url'] = return_url
    return context


def update_timelimit_module(user, course_id, field_data_cache, timelimit_descriptor, timelimit_module):
    """
    Updates the state of the provided timing module, starting it if it hasn't begun.
    Returns dict with timer-related values to enable display of time remaining.
    Returns 'timer_expiration_duration' in dict if timer is still active, and not if timer has expired.
    """
    context = {}
    # determine where to go when the exam ends:
    if timelimit_descriptor.time_expired_redirect_url is None:
        raise Http404("No time_expired_redirect_url specified at this location: {} ".format(timelimit_module.location))
    context['time_expired_redirect_url'] = timelimit_descriptor.time_expired_redirect_url

    if not timelimit_module.has_ended:
        if not timelimit_module.has_begun:
            # user has not started the exam, so start it now.
            if timelimit_descriptor.duration is None:
                raise Http404("No duration specified at this location: {} ".format(timelimit_module.location))
            # The user may have an accommodation that has been granted to them.
            # This accommodation information should already be stored in the module's state.
            timelimit_module.begin(timelimit_descriptor.duration)

        # the exam has been started, either because the student is returning to the
        # exam page, or because they have just visited it.  Fetch the remaining time relative to the
        # end time as stored in the module when it was started.
        context['timer_expiration_duration'] = timelimit_module.get_remaining_time_in_ms()
        # also use the timed module to determine whether top-level navigation is visible:
        context['suppress_toplevel_navigation'] = timelimit_descriptor.suppress_toplevel_navigation
    return context


def chat_settings(course, user):
    """
    Returns a dict containing the settings required to connect to a
    Jabber chat server and room.
    """
    domain = getattr(settings, "JABBER_DOMAIN", None)
    if domain is None:
        log.warning('You must set JABBER_DOMAIN in the settings to '
                    'enable the chat widget')
        return None

    return {
        'domain': domain,

        # Jabber doesn't like slashes, so replace with dashes
        'room': "{ID}_class".format(ID=course.id.replace('/', '-')),

        'username': "{USER}@{DOMAIN}".format(
            USER=user.username, DOMAIN=domain
        ),

        # TODO: clearly this needs to be something other than the username
        #       should also be something that's not necessarily tied to a
        #       particular course
        'password': "{USER}@{DOMAIN}".format(
            USER=user.username, DOMAIN=domain
        ),
    }


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
    user = User.objects.prefetch_related("groups").get(id=request.user.id)
    request.user = user	# keep just one instance of User
    course = get_course_with_access(user, course_id, 'load', depth=2)
    staff_access = has_access(user, course, 'staff')
    registered = registered_for_course(course, user)
    if not registered:
        # TODO (vshnayder): do course instructors need to be registered to see course?
        log.debug('User %s tried to view course %s but is not enrolled' % (user, course.location.url()))
        return redirect(reverse('about_course', args=[course.id]))

    masq = setup_masquerade(request, staff_access)

    try:
        field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
            course.id, user, course, depth=2)

        course_module = get_module_for_descriptor(user, request, course, field_data_cache, course.id)
        if course_module is None:
            log.warning('If you see this, something went wrong: if we got this'
                        ' far, should have gotten a course module for this user')
            return redirect(reverse('about_course', args=[course.id]))

        if chapter is None:
            return redirect_to_course_position(course_module)

        context = {
            'csrf': csrf(request)['csrf_token'],
            'accordion': render_accordion(request, course, chapter, section, field_data_cache),
            'COURSE_TITLE': course.display_name_with_default,
            'course': course,
            'init': '',
            'content': '',
            'staff_access': staff_access,
            'masquerade': masq,
            'xqa_server': settings.MITX_FEATURES.get('USE_XQA_SERVER', 'http://xqa:server@content-qa.mitx.mit.edu/xqa')
            }

        # Only show the chat if it's enabled by the course and in the
        # settings.
        show_chat = course.show_chat and settings.MITX_FEATURES['ENABLE_CHAT']
        if show_chat:
            context['chat'] = chat_settings(course, user)
            # If we couldn't load the chat settings, then don't show
            # the widget in the courseware.
            if context['chat'] is None:
                show_chat = False

        context['show_chat'] = show_chat

        chapter_descriptor = course.get_child_by(lambda m: m.url_name == chapter)
        if chapter_descriptor is not None:
            save_child_position(course_module, chapter)
        else:
            raise Http404('No chapter descriptor found with name {}'.format(chapter))

        chapter_module = course_module.get_child_by(lambda m: m.url_name == chapter)
        if chapter_module is None:
            # User may be trying to access a chapter that isn't live yet
            if masq=='student':  # if staff is masquerading as student be kinder, don't 404
                log.debug('staff masq as student: no chapter %s' % chapter)
                return redirect(reverse('courseware', args=[course.id]))
            raise Http404

        if section is not None:
            section_descriptor = chapter_descriptor.get_child_by(lambda m: m.url_name == section)
            if section_descriptor is None:
                # Specifically asked-for section doesn't exist
                if masq=='student':  # if staff is masquerading as student be kinder, don't 404
                    log.debug('staff masq as student: no section %s' % section)
                    return redirect(reverse('courseware', args=[course.id]))
                raise Http404

            # cdodge: this looks silly, but let's refetch the section_descriptor with depth=None
            # which will prefetch the children more efficiently than doing a recursive load
            section_descriptor = modulestore().get_instance(course.id, section_descriptor.location, depth=None)

            # Load all descendants of the section, because we're going to display its
            # html, which in general will need all of its children
            section_field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
                course_id, user, section_descriptor, depth=None)

            section_module = get_module_for_descriptor(request.user,
                request,
                section_descriptor,
                section_field_data_cache,
                course_id,
                position
            )

            if section_module is None:
                # User may be trying to be clever and access something
                # they don't have access to.
                raise Http404

            # Save where we are in the chapter
            save_child_position(chapter_module, section)

            # check here if this section *is* a timed module.
            if section_module.category == 'timelimit':
                timer_context = update_timelimit_module(user, course_id, student_module_cache,
                                                        section_descriptor, section_module)
                if 'timer_expiration_duration' in timer_context:
                    context.update(timer_context)
                else:
                    # if there is no expiration defined, then we know the timer has expired:
                    return HttpResponseRedirect(timer_context['time_expired_redirect_url'])
            else:
                # check here if this page is within a course that has an active timed module running.  If so, then
                # add in the appropriate timer information to the rendering context:
                context.update(check_for_active_timelimit_module(request, course_id, course))

            context['content'] = section_module.runtime.render(section_module, None, 'student_view').content
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
                              user=user,
                              course=course,
                              chapter=chapter,
                              section=section,
                              position=position
                              ))
            try:
                result = render_to_response('courseware/courseware-error.html',
                                            {'staff_access': staff_access,
                                            'course': course})
            except:
                # Let the exception propagate, relying on global config to at
                # at least return a nice error message
                log.exception("Error while rendering courseware-error page")
                raise

    return result


@ensure_csrf_cookie
def jump_to_id(request, course_id, module_id):
    """
    This entry point allows for a shorter version of a jump to where just the id of the element is
    passed in. This assumes that id is unique within the course_id namespace
    """

    course_location = CourseDescriptor.id_to_location(course_id)

    items = modulestore().get_items(
        ['i4x', course_location.org, course_location.course, None, module_id],
        course_id=course_id
    )

    if len(items) == 0:
        raise Http404("Could not find id = {0} in course_id = {1}. Referer = {2}".
                      format(module_id, course_id, request.META.get("HTTP_REFERER", "")))
    if len(items) > 1:
        log.warning("Multiple items found with id = {0} in course_id = {1}. Referer = {2}. Using first found {3}...".
                    format(module_id, course_id, request.META.get("HTTP_REFERER", ""), items[0].location.url()))

    return jump_to(request, course_id, items[0].location.url())


@ensure_csrf_cookie
def jump_to(request, course_id, location):
    """
    Show the page that contains a specific location.

    If the location is invalid or not in any class, return a 404.

    Otherwise, delegates to the index view to figure out whether this user
    has access, and what they should see.
    """
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

    # choose the appropriate view (and provide the necessary args) based on the
    # args provided by the redirect.
    # Rely on index to do all error handling and access control.
    if chapter is None:
        return redirect('courseware', course_id=course_id)
    elif section is None:
        return redirect('courseware_chapter', course_id=course_id, chapter=chapter)
    elif position is None:
        return redirect('courseware_section', course_id=course_id, chapter=chapter, section=section)
    else:
        return redirect('courseware_position', course_id=course_id, chapter=chapter, section=section, position=position)


@ensure_csrf_cookie
def course_info(request, course_id):
    """
    Display the course's info.html, or 404 if there is no such course.

    Assumes the course_id is in a valid format.
    """
    course = get_course_with_access(request.user, course_id, 'load')
    staff_access = has_access(request.user, course, 'staff')
    masq = setup_masquerade(request, staff_access)    # allow staff to toggle masquerade on info page

    return render_to_response('courseware/info.html', {'request': request, 'course_id': course_id, 'cache': None,
            'course': course, 'staff_access': staff_access, 'masquerade': masq})


@ensure_csrf_cookie
def static_tab(request, course_id, tab_slug):
    """
    Display the courses tab with the given name.

    Assumes the course_id is in a valid format.
    """
    course = get_course_with_access(request.user, course_id, 'load')

    tab = tabs.get_static_tab_by_slug(course, tab_slug)
    if tab is None:
        raise Http404

    contents = tabs.get_static_tab_contents(
        request,
        course,
        tab
    )
    if contents is None:
        raise Http404

    staff_access = has_access(request.user, course, 'staff')
    return render_to_response('courseware/static_tab.html',
                              {'course': course,
                               'tab': tab,
                               'tab_contents': contents,
                               'staff_access': staff_access, })

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
                                            'staff_access': staff_access, })


def registered_for_course(course, user):
    """
    Return True if user is registered for course, else False
    """
    if user is None:
        return False
    if user.is_authenticated():
        return CourseEnrollment.is_enrolled(user, course.id)
    else:
        return False


@ensure_csrf_cookie
@cache_if_anonymous
def course_about(request, course_id):
    if settings.MITX_FEATURES.get('ENABLE_MKTG_SITE', False):
        raise Http404

    course = get_course_with_access(request.user, course_id, 'see_exists')
    registered = registered_for_course(course, request.user)

    if has_access(request.user, course, 'load'):
        course_target = reverse('info', args=[course.id])
    else:
        course_target = reverse('about_course', args=[course.id])

    show_courseware_link = (has_access(request.user, course, 'load') or
                            settings.MITX_FEATURES.get('ENABLE_LMS_MIGRATION'))

    # Note: this is a flow for payment for course registration, not the Verified Certificate flow.
    registration_price = 0
    in_cart = False
    reg_then_add_to_cart_link = ""
    if (settings.MITX_FEATURES.get('ENABLE_SHOPPING_CART') and
        settings.MITX_FEATURES.get('ENABLE_PAID_COURSE_REGISTRATION')):
        registration_price = CourseMode.min_course_price_for_currency(course_id,
                                                                      settings.PAID_COURSE_REGISTRATION_CURRENCY[0])
        if request.user.is_authenticated():
            cart = shoppingcart.models.Order.get_cart_for_user(request.user)
            in_cart = shoppingcart.models.PaidCourseRegistration.contained_in_order(cart, course_id)

        reg_then_add_to_cart_link = "{reg_url}?course_id={course_id}&enrollment_action=add_to_cart".format(
            reg_url=reverse('register_user'), course_id=course.id)

    return render_to_response('courseware/course_about.html',
                              {'course': course,
                               'registered': registered,
                               'course_target': course_target,
                               'registration_price': registration_price,
                               'in_cart': in_cart,
                               'reg_then_add_to_cart_link': reg_then_add_to_cart_link,
                               'show_courseware_link': show_courseware_link})


@ensure_csrf_cookie
@cache_if_anonymous
def mktg_course_about(request, course_id):
    """
    This is the button that gets put into an iframe on the Drupal site
    """

    try:
        course = get_course_with_access(request.user, course_id, 'see_exists')
    except (ValueError, Http404) as e:
        # if a course does not exist yet, display a coming
        # soon button
        return render_to_response('courseware/mktg_coming_soon.html',
                                  {'course_id': course_id})

    registered = registered_for_course(course, request.user)

    if has_access(request.user, course, 'load'):
        course_target = reverse('info', args=[course.id])
    else:
        course_target = reverse('about_course', args=[course.id])

    allow_registration = has_access(request.user, course, 'enroll')

    show_courseware_link = (has_access(request.user, course, 'load') or
                            settings.MITX_FEATURES.get('ENABLE_LMS_MIGRATION'))
    course_modes = CourseMode.modes_for_course(course.id)

    return render_to_response('courseware/mktg_course_about.html',
                              {
                                  'course': course,
                                  'registered': registered,
                                  'allow_registration': allow_registration,
                                  'course_target': course_target,
                                  'show_courseware_link': show_courseware_link,
                                  'course_modes': course_modes,
                              })


def render_notifications(request, course, notifications):
    context = {
        'notifications': notifications,
        'get_discussion_title': partial(get_discussion_title, request=request, course=course),
        'course': course,
    }
    return render_to_string('courseware/notifications.html', context)


@login_required
def news(request, course_id):
    course = get_course_with_access(request.user, course_id, 'load')

    notifications = comment_client.get_notifications(request.user.id)

    context = {
        'course': course,
        'content': render_notifications(request, course, notifications),
    }

    return render_to_response('courseware/news.html', context)


@login_required
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def progress(request, course_id, student_id=None):
    """ User progress. We show the grade bar and every problem score.

    Course staff are allowed to see the progress of students in their class.
    """
    course = get_course_with_access(request.user, course_id, 'load', depth=None)
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

    field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
        course_id, student, course, depth=None)

    courseware_summary = grades.progress_summary(student, request, course,
                                                 field_data_cache)
    grade_summary = grades.grade(student, request, course, field_data_cache)

    if courseware_summary is None:
        #This means the student didn't have access to the course (which the instructor requested)
        raise Http404

    context = {'course': course,
               'courseware_summary': courseware_summary,
               'grade_summary': grade_summary,
               'staff_access': staff_access,
               'student': student,
               }
    context.update()

    return render_to_response('courseware/progress.html', context)


@login_required
def submission_history(request, course_id, student_username, location):
    """Render an HTML fragment (meant for inclusion elsewhere) that renders a
    history of all state changes made by this user for this problem location.
    Right now this only works for problems because that's all
    StudentModuleHistory records.
    """

    course = get_course_with_access(request.user, course_id, 'load')
    staff_access = has_access(request.user, course, 'staff')

    # Permission Denied if they don't have staff access and are trying to see
    # somebody else's submission history.
    if (student_username != request.user.username) and (not staff_access):
        raise PermissionDenied

    try:
        student = User.objects.get(username=student_username)
        student_module = StudentModule.objects.get(course_id=course_id,
                                                   module_state_key=location,
                                                   student_id=student.id)
    except User.DoesNotExist:
        return HttpResponse(escape("User {0} does not exist.".format(student_username)))
    except StudentModule.DoesNotExist:
        return HttpResponse(escape("{0} has never accessed problem {1}".format(student_username, location)))

    history_entries = StudentModuleHistory.objects.filter(
        student_module=student_module
    ).order_by('-id')

    # If no history records exist, let's force a save to get history started.
    if not history_entries:
        student_module.save()
        history_entries = StudentModuleHistory.objects.filter(
            student_module=student_module
        ).order_by('-id')

    context = {
        'history_entries': history_entries,
        'username': student.username,
        'location': location,
        'course_id': course_id
    }

    return render_to_response('courseware/submission_history.html', context)
