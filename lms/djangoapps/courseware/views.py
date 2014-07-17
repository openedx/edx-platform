"""
Courseware views functions
"""

import logging
import urllib
import json

from datetime import datetime
from collections import defaultdict
from django.utils import translation
from django.utils.translation import ugettext as _

from django.conf import settings
from django.core.context_processors import csrf
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.auth.decorators import login_required
from django.utils.timezone import UTC
from django.views.decorators.http import require_GET
from django.http import Http404, HttpResponse
from django.shortcuts import redirect
from edxmako.shortcuts import render_to_response, render_to_string, marketing_link
from django_future.csrf import ensure_csrf_cookie
from django.views.decorators.cache import cache_control
from django.db import transaction
from functools import wraps
from markupsafe import escape

from courseware import grades
from courseware.access import has_access, _adjust_start_date_for_beta_testers
from courseware.courses import get_courses, get_course, get_studio_url, get_course_with_access, sort_by_announcement
from courseware.masquerade import setup_masquerade
from courseware.model_data import FieldDataCache
from .module_render import toc_for_course, get_module_for_descriptor, get_module
from courseware.models import StudentModule, StudentModuleHistory
from course_modes.models import CourseMode

from open_ended_grading import open_ended_notifications
from student.models import UserTestGroup, CourseEnrollment
from student.views import single_course_reverification_info
from util.cache import cache, cache_if_anonymous
from xblock.fragment import Fragment
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError, NoPathToItem
from xmodule.modulestore.search import path_to_location
from xmodule.tabs import CourseTabList, StaffGradingTab, PeerGradingTab, OpenEndedGradingTab
from xmodule.x_module import STUDENT_VIEW
import shoppingcart
from shoppingcart.models import CourseRegistrationCode
from opaque_keys import InvalidKeyError

from microsite_configuration import microsite
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from instructor.enrollment import uses_shib

log = logging.getLogger("edx.courseware")

template_imports = {'urllib': urllib}

CONTENT_DEPTH = 2


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


def verify_course_id(view_func):
    """
    This decorator should only be used with views whose kwargs must contain course_id.
    If course_id is not valid raise 404.
    """

    @wraps(view_func)
    def _decorated(request, *args, **kwargs):
        course_id = kwargs.get("course_id")
        try:
            SlashSeparatedCourseKey.from_deprecated_string(course_id)
        except InvalidKeyError:
            raise Http404
        response = view_func(request, *args, **kwargs)
        return response

    return _decorated


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
    request.user = user	 # keep just one instance of User
    toc = toc_for_course(user, request, course, chapter, section, field_data_cache)

    context = dict([
        ('toc', toc),
        ('course_id', course.id.to_deprecated_string()),
        ('csrf', csrf(request)['csrf_token']),
        ('due_date_display_format', course.due_date_display_format)
    ] + template_imports.items())
    return render_to_string('courseware/accordion.html', context)


def get_current_child(xmodule, min_depth=None):
    """
    Get the xmodule.position's display item of an xmodule that has a position and
    children.  If xmodule has no position or is out of bounds, return the first
    child with children extending down to content_depth.

    For example, if chapter_one has no position set, with two child sections,
    section-A having no children and section-B having a discussion unit,
    `get_current_child(chapter, min_depth=1)`  will return section-B.

    Returns None only if there are no children at all.
    """
    def _get_default_child_module(child_modules):
        """Returns the first child of xmodule, subject to min_depth."""
        if not child_modules:
            default_child = None
        elif not min_depth > 0:
            default_child = child_modules[0]
        else:
            content_children = [child for child in child_modules if
                                child.has_children_at_depth(min_depth - 1) and child.get_display_items()]
            default_child = content_children[0] if content_children else None

        return default_child

    if not hasattr(xmodule, 'position'):
        return None

    if xmodule.position is None:
        return _get_default_child_module(xmodule.get_display_items())
    else:
        # position is 1-indexed.
        pos = xmodule.position - 1

    children = xmodule.get_display_items()
    if 0 <= pos < len(children):
        child = children[pos]
    elif len(children) > 0:
        # module has a set position, but the position is out of range.
        # return default child.
        child = _get_default_child_module(children)
    else:
        child = None
    return child


def redirect_to_course_position(course_module, content_depth):
    """
    Return a redirect to the user's current place in the course.

    If this is the user's first time, redirects to COURSE/CHAPTER/SECTION.
    If this isn't the users's first time, redirects to COURSE/CHAPTER,
    and the view will find the current section and display a message
    about reusing the stored position.

    If there is no current position in the course or chapter, then selects
    the first child.

    """
    urlargs = {'course_id': course_module.id.to_deprecated_string()}
    chapter = get_current_child(course_module, min_depth=content_depth)
    if chapter is None:
        # oops.  Something bad has happened.
        raise Http404("No chapter found when loading current position in course")

    urlargs['chapter'] = chapter.url_name
    if course_module.position is not None:
        return redirect(reverse('courseware_chapter', kwargs=urlargs))

    # Relying on default of returning first child
    section = get_current_child(chapter, min_depth=content_depth - 1)
    if section is None:
        raise Http404("No section found when loading current position in course")

    urlargs['section'] = section.url_name
    return redirect(reverse('courseware_section', kwargs=urlargs))


def save_child_position(seq_module, child_name):
    """
    child_name: url_name of the child
    """
    for position, c in enumerate(seq_module.get_display_items(), start=1):
        if c.location.name == child_name:
            # Only save if position changed
            if position != seq_module.position:
                seq_module.position = position
    # Save this new position to the underlying KeyValueStore
    seq_module.save()


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
@verify_course_id
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

    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)

    user = User.objects.prefetch_related("groups").get(id=request.user.id)

    # Redirecting to dashboard if the course is blocked due to un payment.
    redeemed_registration_codes = CourseRegistrationCode.objects.filter(course_id=course_key, registrationcoderedemption__redeemed_by=request.user)
    for redeemed_registration in redeemed_registration_codes:
        if not getattr(redeemed_registration.invoice, 'is_valid'):
            log.warning(u'User %s cannot access the course %s because payment has not yet been received', user, course_key.to_deprecated_string())
            return redirect(reverse('dashboard'))

    request.user = user  # keep just one instance of User
    course = get_course_with_access(user, 'load', course_key, depth=2)
    staff_access = has_access(user, 'staff', course)
    registered = registered_for_course(course, user)
    if not registered:
        # TODO (vshnayder): do course instructors need to be registered to see course?
        log.debug(u'User %s tried to view course %s but is not enrolled', user, course.location.to_deprecated_string())
        return redirect(reverse('about_course', args=[course_key.to_deprecated_string()]))

    masq = setup_masquerade(request, staff_access)

    try:
        field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
            course_key, user, course, depth=2)

        course_module = get_module_for_descriptor(user, request, course, field_data_cache, course_key)
        if course_module is None:
            log.warning(u'If you see this, something went wrong: if we got this'
                        u' far, should have gotten a course module for this user')
            return redirect(reverse('about_course', args=[course_key.to_deprecated_string()]))

        studio_url = get_studio_url(course, 'course')

        context = {
            'csrf': csrf(request)['csrf_token'],
            'accordion': render_accordion(request, course, chapter, section, field_data_cache),
            'COURSE_TITLE': course.display_name_with_default,
            'course': course,
            'init': '',
            'fragment': Fragment(),
            'staff_access': staff_access,
            'studio_url': studio_url,
            'masquerade': masq,
            'xqa_server': settings.FEATURES.get('USE_XQA_SERVER', 'http://xqa:server@content-qa.mitx.mit.edu/xqa'),
            'reverifications': fetch_reverify_banner_info(request, course_key),
        }

        now = datetime.now(UTC())
        effective_start = _adjust_start_date_for_beta_testers(user, course, course_key)
        if staff_access and now < effective_start:
            # Disable student view button if user is staff and
            # course is not yet visible to students.
            context['disable_student_access'] = True

        has_content = course.has_children_at_depth(CONTENT_DEPTH)
        if not has_content:
            # Show empty courseware for a course with no units
            return render_to_response('courseware/courseware.html', context)
        elif chapter is None:
            # passing CONTENT_DEPTH avoids returning 404 for a course with an
            # empty first section and a second section with content
            return redirect_to_course_position(course_module, CONTENT_DEPTH)

        # Only show the chat if it's enabled by the course and in the
        # settings.
        show_chat = course.show_chat and settings.FEATURES['ENABLE_CHAT']
        if show_chat:
            context['chat'] = chat_settings(course, user)
            # If we couldn't load the chat settings, then don't show
            # the widget in the courseware.
            if context['chat'] is None:
                show_chat = False

        context['show_chat'] = show_chat

        chapter_descriptor = course.get_child_by(lambda m: m.location.name == chapter)
        if chapter_descriptor is not None:
            save_child_position(course_module, chapter)
        else:
            raise Http404('No chapter descriptor found with name {}'.format(chapter))

        chapter_module = course_module.get_child_by(lambda m: m.location.name == chapter)
        if chapter_module is None:
            # User may be trying to access a chapter that isn't live yet
            if masq == 'student':  # if staff is masquerading as student be kinder, don't 404
                log.debug('staff masq as student: no chapter %s' % chapter)
                return redirect(reverse('courseware', args=[course.id.to_deprecated_string()]))
            raise Http404

        if section is not None:
            section_descriptor = chapter_descriptor.get_child_by(lambda m: m.location.name == section)

            if section_descriptor is None:
                # Specifically asked-for section doesn't exist
                if masq == 'student':  # if staff is masquerading as student be kinder, don't 404
                    log.debug('staff masq as student: no section %s' % section)
                    return redirect(reverse('courseware', args=[course.id.to_deprecated_string()]))
                raise Http404

            ## Allow chromeless operation
            if section_descriptor.chrome:
                chrome = [s.strip() for s in section_descriptor.chrome.lower().split(",")]
                if 'accordion' not in chrome:
                    context['disable_accordion'] = True
                if 'tabs' not in chrome:
                    context['disable_tabs'] = True

            if section_descriptor.default_tab:
                context['default_tab'] = section_descriptor.default_tab

            # cdodge: this looks silly, but let's refetch the section_descriptor with depth=None
            # which will prefetch the children more efficiently than doing a recursive load
            section_descriptor = modulestore().get_item(section_descriptor.location, depth=None)

            # Load all descendants of the section, because we're going to display its
            # html, which in general will need all of its children
            section_field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
                course_key, user, section_descriptor, depth=None)

            # Verify that position a string is in fact an int
            if position is not None:
                try:
                    int(position)
                except ValueError:
                    raise Http404("Position {} is not an integer!".format(position))

            section_module = get_module_for_descriptor(
                request.user,
                request,
                section_descriptor,
                section_field_data_cache,
                course_key,
                position
            )

            if section_module is None:
                # User may be trying to be clever and access something
                # they don't have access to.
                raise Http404

            # Save where we are in the chapter
            save_child_position(chapter_module, section)
            context['fragment'] = section_module.render(STUDENT_VIEW)
            context['section_title'] = section_descriptor.display_name_with_default
        else:
            # section is none, so display a message
            studio_url = get_studio_url(course, 'course')
            prev_section = get_current_child(chapter_module)
            if prev_section is None:
                # Something went wrong -- perhaps this chapter has no sections visible to the user.
                # Clearing out the last-visited state and showing "first-time" view by redirecting
                # to courseware.
                course_module.position = None
                course_module.save()
                return redirect(reverse('courseware', args=[course.id.to_deprecated_string()]))
            prev_section_url = reverse('courseware_section', kwargs={
                'course_id': course_key.to_deprecated_string(),
                'chapter': chapter_descriptor.url_name,
                'section': prev_section.url_name
            })
            context['fragment'] = Fragment(content=render_to_string(
                'courseware/welcome-back.html',
                {
                    'course': course,
                    'studio_url': studio_url,
                    'chapter_module': chapter_module,
                    'prev_section': prev_section,
                    'prev_section_url': prev_section_url
                }
            ))

        result = render_to_response('courseware/courseware.html', context)
    except Exception as e:

        # Doesn't bar Unicode characters from URL, but if Unicode characters do
        # cause an error it is a graceful failure.
        if isinstance(e, UnicodeEncodeError):
            raise Http404("URL contains Unicode characters")

        if isinstance(e, Http404):
            # let it propagate
            raise

        # In production, don't want to let a 500 out for any reason
        if settings.DEBUG:
            raise
        else:
            log.exception(
                u"Error in index view: user={user}, course={course}, chapter={chapter}"
                u" section={section} position={position}".format(
                    user=user,
                    course=course,
                    chapter=chapter,
                    section=section,
                    position=position
                ))
            try:
                result = render_to_response('courseware/courseware-error.html', {
                    'staff_access': staff_access,
                    'course': course
                })
            except:
                # Let the exception propagate, relying on global config to at
                # at least return a nice error message
                log.exception("Error while rendering courseware-error page")
                raise

    return result


@ensure_csrf_cookie
@verify_course_id
def jump_to_id(request, course_id, module_id):
    """
    This entry point allows for a shorter version of a jump to where just the id of the element is
    passed in. This assumes that id is unique within the course_id namespace
    """
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    items = modulestore().get_items(course_key, qualifiers={'name': module_id})

    if len(items) == 0:
        raise Http404(
            u"Could not find id: {0} in course_id: {1}. Referer: {2}".format(
                module_id, course_id, request.META.get("HTTP_REFERER", "")
            ))
    if len(items) > 1:
        log.warning(
            u"Multiple items found with id: {0} in course_id: {1}. Referer: {2}. Using first: {3}".format(
                module_id, course_id, request.META.get("HTTP_REFERER", ""), items[0].location.to_deprecated_string()
            ))

    return jump_to(request, course_id, items[0].location.to_deprecated_string())


@ensure_csrf_cookie
def jump_to(request, course_id, location):
    """
    Show the page that contains a specific location.

    If the location is invalid or not in any class, return a 404.

    Otherwise, delegates to the index view to figure out whether this user
    has access, and what they should see.
    """
    try:
        course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
        usage_key = course_key.make_usage_key_from_deprecated_string(location)
    except InvalidKeyError:
        raise Http404(u"Invalid course_key or usage_key")
    try:
        (course_key, chapter, section, position) = path_to_location(modulestore(), usage_key)
    except ItemNotFoundError:
        raise Http404(u"No data at this location: {0}".format(usage_key))
    except NoPathToItem:
        raise Http404(u"This location is not in any class: {0}".format(usage_key))

    # choose the appropriate view (and provide the necessary args) based on the
    # args provided by the redirect.
    # Rely on index to do all error handling and access control.
    if chapter is None:
        return redirect('courseware', course_id=course_key.to_deprecated_string())
    elif section is None:
        return redirect('courseware_chapter', course_id=course_key.to_deprecated_string(), chapter=chapter)
    elif position is None:
        return redirect('courseware_section', course_id=course_key.to_deprecated_string(), chapter=chapter, section=section)
    else:
        return redirect('courseware_position', course_id=course_key.to_deprecated_string(), chapter=chapter, section=section, position=position)


@ensure_csrf_cookie
@verify_course_id
def course_info(request, course_id):
    """
    Display the course's info.html, or 404 if there is no such course.

    Assumes the course_id is in a valid format.
    """

    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)

    course = get_course_with_access(request.user, 'load', course_key)
    staff_access = has_access(request.user, 'staff', course)
    masq = setup_masquerade(request, staff_access)    # allow staff to toggle masquerade on info page
    reverifications = fetch_reverify_banner_info(request, course_key)
    studio_url = get_studio_url(course, 'course_info')

    # link to where the student should go to enroll in the course:
    # about page if there is not marketing site, SITE_NAME if there is
    url_to_enroll = reverse(course_about, args=[course_id])
    if settings.FEATURES.get('ENABLE_MKTG_SITE'):
        url_to_enroll = marketing_link('COURSES')

    show_enroll_banner = request.user.is_authenticated() and not CourseEnrollment.is_enrolled(request.user, course.id)

    context = {
        'request': request,
        'course_id': course_key.to_deprecated_string(),
        'cache': None,
        'course': course,
        'staff_access': staff_access,
        'masquerade': masq,
        'studio_url': studio_url,
        'reverifications': reverifications,
        'show_enroll_banner': show_enroll_banner,
        'url_to_enroll': url_to_enroll,
    }

    now = datetime.now(UTC())
    effective_start = _adjust_start_date_for_beta_testers(request.user, course, course_key)
    if staff_access and now < effective_start:
        # Disable student view button if user is staff and
        # course is not yet visible to students.
        context['disable_student_access'] = True

    return render_to_response('courseware/info.html', context)


@ensure_csrf_cookie
@verify_course_id
def static_tab(request, course_id, tab_slug):
    """
    Display the courses tab with the given name.

    Assumes the course_id is in a valid format.
    """

    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)

    course = get_course_with_access(request.user, 'load', course_key)

    tab = CourseTabList.get_tab_by_slug(course.tabs, tab_slug)
    if tab is None:
        raise Http404

    contents = get_static_tab_contents(
        request,
        course,
        tab
    )
    if contents is None:
        raise Http404

    return render_to_response('courseware/static_tab.html', {
        'course': course,
        'tab': tab,
        'tab_contents': contents,
    })

# TODO arjun: remove when custom tabs in place, see courseware/syllabus.py


@ensure_csrf_cookie
@verify_course_id
def syllabus(request, course_id):
    """
    Display the course's syllabus.html, or 404 if there is no such course.

    Assumes the course_id is in a valid format.
    """

    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)

    course = get_course_with_access(request.user, 'load', course_key)
    staff_access = has_access(request.user, 'staff', course)

    return render_to_response('courseware/syllabus.html', {
        'course': course,
        'staff_access': staff_access,
    })


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
    """
    Display the course's about page.

    Assumes the course_id is in a valid format.
    """

    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    course = get_course_with_access(request.user, 'see_exists', course_key)

    if microsite.get_value(
        'ENABLE_MKTG_SITE',
        settings.FEATURES.get('ENABLE_MKTG_SITE', False)
    ):
        return redirect(reverse('info', args=[course.id.to_deprecated_string()]))

    registered = registered_for_course(course, request.user)
    staff_access = has_access(request.user, 'staff', course)
    studio_url = get_studio_url(course, 'settings/details')

    if has_access(request.user, 'load', course):
        course_target = reverse('info', args=[course.id.to_deprecated_string()])
    else:
        course_target = reverse('about_course', args=[course.id.to_deprecated_string()])

    show_courseware_link = (has_access(request.user, 'load', course) or
                            settings.FEATURES.get('ENABLE_LMS_MIGRATION'))

    # Note: this is a flow for payment for course registration, not the Verified Certificate flow.
    registration_price = 0
    in_cart = False
    reg_then_add_to_cart_link = ""
    if (settings.FEATURES.get('ENABLE_SHOPPING_CART') and
        settings.FEATURES.get('ENABLE_PAID_COURSE_REGISTRATION')):
        registration_price = CourseMode.min_course_price_for_currency(course_key,
                                                                      settings.PAID_COURSE_REGISTRATION_CURRENCY[0])
        if request.user.is_authenticated():
            cart = shoppingcart.models.Order.get_cart_for_user(request.user)
            in_cart = shoppingcart.models.PaidCourseRegistration.contained_in_order(cart, course_key)

        reg_then_add_to_cart_link = "{reg_url}?course_id={course_id}&enrollment_action=add_to_cart".format(
            reg_url=reverse('register_user'), course_id=course.id.to_deprecated_string())

    # Used to provide context to message to student if enrollment not allowed
    can_enroll = has_access(request.user, 'enroll', course)
    invitation_only = course.invitation_only
    is_course_full = CourseEnrollment.is_course_full(course)

    # Register button should be disabled if one of the following is true:
    # - Student is already registered for course
    # - Course is already full
    # - Student cannot enroll in course
    active_reg_button = not(registered or is_course_full or not can_enroll)

    is_shib_course = uses_shib(course)

    return render_to_response('courseware/course_about.html', {
        'course': course,
        'staff_access': staff_access,
        'studio_url': studio_url,
        'registered': registered,
        'course_target': course_target,
        'registration_price': registration_price,
        'in_cart': in_cart,
        'reg_then_add_to_cart_link': reg_then_add_to_cart_link,
        'show_courseware_link': show_courseware_link,
        'is_course_full': is_course_full,
        'can_enroll': can_enroll,
        'invitation_only': invitation_only,
        'active_reg_button': active_reg_button,
        'is_shib_course': is_shib_course,
    })


@ensure_csrf_cookie
@cache_if_anonymous
@verify_course_id
def mktg_course_about(request, course_id):
    """
    This is the button that gets put into an iframe on the Drupal site
    """

    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)

    try:
        course = get_course_with_access(request.user, 'see_exists', course_key)
    except (ValueError, Http404) as e:
        # if a course does not exist yet, display a coming
        # soon button
        return render_to_response(
            'courseware/mktg_coming_soon.html', {'course_id': course_key.to_deprecated_string()}
        )

    registered = registered_for_course(course, request.user)

    if has_access(request.user, 'load', course):
        course_target = reverse('info', args=[course.id.to_deprecated_string()])
    else:
        course_target = reverse('about_course', args=[course.id.to_deprecated_string()])

    allow_registration = has_access(request.user, 'enroll', course)

    show_courseware_link = (has_access(request.user, 'load', course) or
                            settings.FEATURES.get('ENABLE_LMS_MIGRATION'))
    course_modes = CourseMode.modes_for_course_dict(course.id)

    context = {
        'course': course,
        'registered': registered,
        'allow_registration': allow_registration,
        'course_target': course_target,
        'show_courseware_link': show_courseware_link,
        'course_modes': course_modes,
    }

    # The edx.org marketing site currently displays only in English.
    # To avoid displaying a different language in the register / access button,
    # we force the language to English.
    # However, OpenEdX installations with a different marketing front-end
    # may want to respect the language specified by the user or the site settings.
    force_english = settings.FEATURES.get('IS_EDX_DOMAIN', False)
    if force_english:
        translation.activate('en-us')

    try:
        return render_to_response('courseware/mktg_course_about.html', context)
    finally:
        # Just to be safe, reset the language if we forced it to be English.
        if force_english:
            translation.deactivate()

@login_required
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@transaction.commit_manually
@verify_course_id
def progress(request, course_id, student_id=None):
    """
    Wraps "_progress" with the manual_transaction context manager just in case
    there are unanticipated errors.
    """

    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)

    with grades.manual_transaction():
        return _progress(request, course_key, student_id)


def _progress(request, course_key, student_id):
    """
    Unwrapped version of "progress".

    User progress. We show the grade bar and every problem score.

    Course staff are allowed to see the progress of students in their class.
    """
    course = get_course_with_access(request.user, 'load', course_key, depth=None, check_if_enrolled=True)
    staff_access = has_access(request.user, 'staff', course)

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

    courseware_summary = grades.progress_summary(student, request, course)
    studio_url = get_studio_url(course, 'settings/grading')
    grade_summary = grades.grade(student, request, course)

    if courseware_summary is None:
        #This means the student didn't have access to the course (which the instructor requested)
        raise Http404

    context = {
        'course': course,
        'courseware_summary': courseware_summary,
        'studio_url': studio_url,
        'grade_summary': grade_summary,
        'staff_access': staff_access,
        'student': student,
        'reverifications': fetch_reverify_banner_info(request, course_key)
    }

    with grades.manual_transaction():
        response = render_to_response('courseware/progress.html', context)

    return response


def fetch_reverify_banner_info(request, course_key):
    """
    Fetches needed context variable to display reverification banner in courseware
    """
    reverifications = defaultdict(list)
    user = request.user
    if not user.id:
        return reverifications
    enrollment = CourseEnrollment.get_or_create_enrollment(request.user, course_key)
    course = modulestore().get_course(course_key)
    info = single_course_reverification_info(user, course, enrollment)
    if info:
        reverifications[info.status].append(info)
    return reverifications


@login_required
@verify_course_id
def submission_history(request, course_id, student_username, location):
    """Render an HTML fragment (meant for inclusion elsewhere) that renders a
    history of all state changes made by this user for this problem location.
    Right now this only works for problems because that's all
    StudentModuleHistory records.
    """

    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)

    try:
        usage_key = course_key.make_usage_key_from_deprecated_string(location)
    except (InvalidKeyError, AssertionError):
        return HttpResponse(escape(_(u'Invalid location.')))

    course = get_course_with_access(request.user, 'load', course_key)
    staff_access = has_access(request.user, 'staff', course)

    # Permission Denied if they don't have staff access and are trying to see
    # somebody else's submission history.
    if (student_username != request.user.username) and (not staff_access):
        raise PermissionDenied

    try:
        student = User.objects.get(username=student_username)
        student_module = StudentModule.objects.get(
            course_id=course_key,
            module_state_key=usage_key,
            student_id=student.id
        )
    except User.DoesNotExist:
        return HttpResponse(escape(_(u'User {username} does not exist.').format(username=student_username)))
    except StudentModule.DoesNotExist:
        return HttpResponse(escape(_(u'User {username} has never accessed problem {location}').format(
            username=student_username,
            location=location
        )))
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
        'course_id': course_key.to_deprecated_string()
    }

    return render_to_response('courseware/submission_history.html', context)


def notification_image_for_tab(course_tab, user, course):
    """
    Returns the notification image path for the given course_tab if applicable, otherwise None.
    """

    tab_notification_handlers = {
        StaffGradingTab.type: open_ended_notifications.staff_grading_notifications,
        PeerGradingTab.type: open_ended_notifications.peer_grading_notifications,
        OpenEndedGradingTab.type: open_ended_notifications.combined_notifications
    }

    if course_tab.type in tab_notification_handlers:
        notifications = tab_notification_handlers[course_tab.type](course, user)
        if notifications and notifications['pending_grading']:
            return notifications['img_path']

    return None


def get_static_tab_contents(request, course, tab):
    """
    Returns the contents for the given static tab
    """
    loc = course.id.make_usage_key(
        tab.type,
        tab.url_slug,
    )
    field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
        course.id, request.user, modulestore().get_item(loc), depth=0
    )
    tab_module = get_module(
        request.user, request, loc, field_data_cache, static_asset_path=course.static_asset_path
    )

    logging.debug('course_module = {0}'.format(tab_module))

    html = ''
    if tab_module is not None:
        try:
            html = tab_module.render(STUDENT_VIEW).content
        except Exception:  # pylint: disable=broad-except
            html = render_to_string('courseware/error-message.html', None)
            log.exception(
                u"Error rendering course={course}, tab={tab_url}".format(course=course, tab_url=tab['url_slug'])
            )

    return html


@require_GET
@verify_course_id
def get_course_lti_endpoints(request, course_id):
    """
    View that, given a course_id, returns the a JSON object that enumerates all of the LTI endpoints for that course.

    The LTI 2.0 result service spec at
    http://www.imsglobal.org/lti/ltiv2p0/uml/purl.imsglobal.org/vocab/lis/v2/outcomes/Result/service.html
    says "This specification document does not prescribe a method for discovering the endpoint URLs."  This view
    function implements one way of discovering these endpoints, returning a JSON array when accessed.

    Arguments:
        request (django request object):  the HTTP request object that triggered this view function
        course_id (unicode):  id associated with the course

    Returns:
        (django response object):  HTTP response.  404 if course is not found, otherwise 200 with JSON body.
    """

    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)

    try:
        course = get_course(course_key, depth=2)
    except ValueError:
        return HttpResponse(status=404)

    anonymous_user = AnonymousUser()
    anonymous_user.known = False  # make these "noauth" requests like module_render.handle_xblock_callback_noauth
    lti_descriptors = modulestore().get_items(course.id, qualifiers={'category': 'lti'})

    lti_noauth_modules = [
        get_module_for_descriptor(
            anonymous_user,
            request,
            descriptor,
            FieldDataCache.cache_for_descriptor_descendents(
                course_key,
                anonymous_user,
                descriptor
            ),
            course_key
        )
        for descriptor in lti_descriptors
    ]

    endpoints = [
        {
            'display_name': module.display_name,
            'lti_2_0_result_service_json_endpoint': module.get_outcome_service_url(
                service_name='lti_2_0_result_rest_handler') + "/user/{anon_user_id}",
            'lti_1_1_result_service_xml_endpoint': module.get_outcome_service_url(
                service_name='grade_handler'),
        }
        for module in lti_noauth_modules
    ]

    return HttpResponse(json.dumps(endpoints), content_type='application/json')
