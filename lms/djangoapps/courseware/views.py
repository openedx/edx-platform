"""
Courseware views functions
"""

import json
import logging
import urllib
from util.json_request import JsonResponse
from pytz import timezone

from collections import OrderedDict
from datetime import datetime

import analytics
import newrelic.agent
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, AnonymousUser
from django.core.context_processors import csrf
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseNotFound, HttpResponseServerError
from django.http import Http404, HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import redirect
from django.utils.timezone import UTC
from django.utils.translation import ugettext as _
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from eventtracking import tracker
from ipware.ip import get_ip
from markupsafe import escape
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey, UsageKey
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from rest_framework import status
from xblock.fragment import Fragment

import shoppingcart
import survey.utils
import survey.views
from certificates import api as certs_api
from openedx.core.lib.gating import api as gating_api
from course_modes.models import CourseMode
from courseware import grades
from courseware.access import has_access, has_ccx_coach_role, _adjust_start_date_for_beta_testers
from courseware.access_response import StartDateError
from courseware.access_utils import in_preview_mode
from courseware.courses import (
    get_courses,
    get_course,
    get_course_by_id,
    get_permission_for_course_about,
    get_studio_url,
    get_course_overview_with_access,
    get_course_with_access,
    sort_by_announcement,
    sort_by_start_date,
    UserNotEnrolled
)
from courseware.masquerade import setup_masquerade
from courseware.models import CoursePreference
from courseware.model_data import FieldDataCache, ScoresClient
from courseware.models import StudentModuleHistory
from courseware.url_helpers import get_redirect_url
from courseware.user_state_client import DjangoXBlockUserStateClient
from edxmako.shortcuts import render_to_response, render_to_string, marketing_link
from instructor.enrollment import uses_shib
from microsite_configuration import microsite
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.credit.api import (
    get_credit_requirement_status,
    is_user_eligible_for_credit,
    is_credit_course
)
from student.models import UserProfile
from shoppingcart.models import CourseRegistrationCode
from shoppingcart.utils import is_shopping_cart_enabled
from openedx.core.djangoapps.self_paced.models import SelfPacedConfiguration
from student.models import UserTestGroup, CourseEnrollment
from student.views import is_course_blocked
from util.cache import cache, cache_if_anonymous
from util.date_utils import strftime_localized
from util.db import outer_atomic
from util.milestones_helpers import get_prerequisite_courses_display
from util.views import _record_feedback_in_zendesk
from util.views import ensure_valid_course_key
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError, NoPathToItem
from xmodule.tabs import CourseTabList
from xmodule.x_module import STUDENT_VIEW
from util.date_utils import get_time_display

from analyticsclient.client import Client
from analyticsclient.exceptions import NotFoundError, InvalidRequestError, TimeoutError
from lms.djangoapps.ccx.custom_exception import CCXLocatorValidationException
from .entrance_exams import (
    course_has_entrance_exam,
    get_entrance_exam_content,
    get_entrance_exam_score,
    user_must_complete_entrance_exam,
    user_has_passed_entrance_exam
)
from .module_render import toc_for_course, get_module_for_descriptor, get_module, get_module_by_usage_id

from lang_pref import LANGUAGE_KEY
from openedx.core.djangoapps.user_api.preferences.api import get_user_preference


log = logging.getLogger("edx.courseware")

template_imports = {'urllib': urllib}

CONTENT_DEPTH = 2
# Only display the requirements on learner dashboard for
# credit and verified modes.
REQUIREMENTS_DISPLAY_MODES = CourseMode.CREDIT_MODES + [CourseMode.VERIFIED]


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
@cache_if_anonymous()
def courses(request):
    """
    Render "find courses" page.  The course selection work is done in courseware.courses.
    """
    courses_list = []
    course_discovery_meanings = getattr(settings, 'COURSE_DISCOVERY_MEANINGS', {})
    if not settings.FEATURES.get('ENABLE_COURSE_DISCOVERY'):
        courses_list = get_courses(request.user)

        if microsite.get_value("ENABLE_COURSE_SORTING_BY_START_DATE",
                               settings.FEATURES["ENABLE_COURSE_SORTING_BY_START_DATE"]):
            courses_list = sort_by_start_date(courses_list)
        else:
            courses_list = sort_by_announcement(courses_list)

    return render_to_response(
        "courseware/courses.html",
        {'courses': courses_list, 'course_discovery_meanings': course_discovery_meanings}
    )


def render_accordion(user, request, course, chapter, section, field_data_cache):
    """
    Draws navigation bar. Takes current position in accordion as
    parameter.

    If chapter and section are '' or None, renders a default accordion.

    course, chapter, and section are the url_names.

    Returns the html string
    """
    # grab the table of contents
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


def save_positions_recursively_up(user, request, field_data_cache, xmodule, course=None):
    """
    Recurses up the course tree starting from a leaf
    Saving the position property based on the previous node as it goes
    """
    current_module = xmodule

    while current_module:
        parent_location = modulestore().get_parent_location(current_module.location)
        parent = None
        if parent_location:
            parent_descriptor = modulestore().get_item(parent_location)
            parent = get_module_for_descriptor(
                user,
                request,
                parent_descriptor,
                field_data_cache,
                current_module.location.course_key,
                course=course
            )

        if parent and hasattr(parent, 'position'):
            save_child_position(parent, current_module.location.name)

        current_module = parent


@transaction.non_atomic_requests
@login_required
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@ensure_valid_course_key
@outer_atomic(read_committed=True)
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

    course_key = CourseKey.from_string(course_id)

    # Gather metrics for New Relic so we can slice data in New Relic Insights
    newrelic.agent.add_custom_parameter('course_id', unicode(course_key))
    newrelic.agent.add_custom_parameter('org', unicode(course_key.org))

    user = User.objects.prefetch_related("groups").get(id=request.user.id)

    redeemed_registration_codes = CourseRegistrationCode.objects.filter(
        course_id=course_key,
        registrationcoderedemption__redeemed_by=request.user
    )

    # Redirect to dashboard if the course is blocked due to non-payment.
    if is_course_blocked(request, redeemed_registration_codes, course_key):
        # registration codes may be generated via Bulk Purchase Scenario
        # we have to check only for the invoice generated registration codes
        # that their invoice is valid or not
        log.warning(
            u'User %s cannot access the course %s because payment has not yet been received',
            user,
            course_key.to_deprecated_string()
        )
        return redirect(reverse('dashboard'))

    request.user = user  # keep just one instance of User
    with modulestore().bulk_operations(course_key):
        return _index_bulk_op(request, course_key, chapter, section, position)


# pylint: disable=too-many-statements
def _index_bulk_op(request, course_key, chapter, section, position):
    """
    Render the index page for the specified course.
    """
    # Verify that position a string is in fact an int
    if position is not None:
        try:
            int(position)
        except ValueError:
            raise Http404(u"Position {} is not an integer!".format(position))

    course = get_course_with_access(request.user, 'load', course_key, depth=2)
    staff_access = has_access(request.user, 'staff', course)
    masquerade, user = setup_masquerade(request, course_key, staff_access, reset_masquerade_data=True)

    registered = registered_for_course(course, user)
    if not registered:
        # TODO (vshnayder): do course instructors need to be registered to see course?
        log.debug(u'User %s tried to view course %s but is not enrolled', user, course.location.to_deprecated_string())
        return redirect(reverse('about_course', args=[course_key.to_deprecated_string()]))

    # see if all pre-requisites (as per the milestones app feature) have been fulfilled
    # Note that if the pre-requisite feature flag has been turned off (default) then this check will
    # always pass
    if not has_access(user, 'view_courseware_with_prerequisites', course):
        # prerequisites have not been fulfilled therefore redirect to the Dashboard
        log.info(
            u'User %d tried to view course %s '
            u'without fulfilling prerequisites',
            user.id, unicode(course.id))
        return redirect(reverse('dashboard'))

    # Entrance Exam Check
    # If the course has an entrance exam and the requested chapter is NOT the entrance exam, and
    # the user hasn't yet met the criteria to bypass the entrance exam, redirect them to the exam.
    if chapter and course_has_entrance_exam(course):
        chapter_descriptor = course.get_child_by(lambda m: m.location.name == chapter)
        if chapter_descriptor and not getattr(chapter_descriptor, 'is_entrance_exam', False) \
                and user_must_complete_entrance_exam(request, user, course):
            log.info(u'User %d tried to view course %s without passing entrance exam', user.id, unicode(course.id))
            return redirect(reverse('courseware', args=[unicode(course.id)]))

    # Gated Content Check
    gated_content = gating_api.get_gated_content(course, user)
    if section and gated_content:
        for usage_key in gated_content:
            if section in usage_key:
                raise Http404

    # check to see if there is a required survey that must be taken before
    # the user can access the course.
    if survey.utils.must_answer_survey(course, user):
        return redirect(reverse('course_survey', args=[unicode(course.id)]))

    bookmarks_api_url = reverse('bookmarks')

    try:
        field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
            course_key, user, course, depth=2)

        course_module = get_module_for_descriptor(
            user, request, course, field_data_cache, course_key, course=course
        )
        if course_module is None:
            log.warning(u'If you see this, something went wrong: if we got this'
                        u' far, should have gotten a course module for this user')
            return redirect(reverse('about_course', args=[course_key.to_deprecated_string()]))

        studio_url = get_studio_url(course, 'course')

        analytics_url = getattr(settings, 'ANALYTICS_DATA_URL')
        language_preference = get_user_preference(request.user, LANGUAGE_KEY)
        if not language_preference:
            language_preference = settings.LANGUAGE_CODE

        context = {
            'csrf': csrf(request)['csrf_token'],
            'accordion': render_accordion(user, request, course, chapter, section, field_data_cache),
            'COURSE_TITLE': course.display_name_with_default_escaped,
            'course': course,
            'init': '',
            'fragment': Fragment(),
            'staff_access': staff_access,
            'studio_url': studio_url,
            'masquerade': masquerade,
            'analytics_url': analytics_url,
            'xqa_server': settings.FEATURES.get('XQA_SERVER', "http://your_xqa_server.com"),
            'bookmarks_api_url': bookmarks_api_url,
            'language_preference': language_preference,
            'disable_optimizely': True,
        }

        now = datetime.now(UTC())
        effective_start = _adjust_start_date_for_beta_testers(user, course, course_key)
        if not in_preview_mode() and staff_access and now < effective_start:
            # Disable student view button if user is staff and
            # course is not yet visible to students.
            context['disable_student_access'] = True

        has_content = course.has_children_at_depth(CONTENT_DEPTH)
        if not has_content:
            # Show empty courseware for a course with no units
            return render_to_response('courseware/courseware.html', context)
        elif chapter is None:
            # Check first to see if we should instead redirect the user to an Entrance Exam
            if course_has_entrance_exam(course):
                exam_chapter = get_entrance_exam_content(request, course)
                if exam_chapter:
                    exam_section = None
                    if exam_chapter.get_children():
                        exam_section = exam_chapter.get_children()[0]
                        if exam_section:
                            return redirect('courseware_section',
                                            course_id=unicode(course_key),
                                            chapter=exam_chapter.url_name,
                                            section=exam_section.url_name)

            # passing CONTENT_DEPTH avoids returning 404 for a course with an
            # empty first section and a second section with content
            return redirect_to_course_position(course_module, CONTENT_DEPTH)

        chapter_descriptor = course.get_child_by(lambda m: m.location.name == chapter)
        if chapter_descriptor is not None:
            save_child_position(course_module, chapter)
        else:
            raise Http404('No chapter descriptor found with name {}'.format(chapter))

        chapter_module = course_module.get_child_by(lambda m: m.location.name == chapter)
        if chapter_module is None:
            # User may be trying to access a chapter that isn't live yet
            if masquerade and masquerade.role == 'student':  # if staff is masquerading as student be kinder, don't 404
                log.debug('staff masquerading as student: no chapter %s', chapter)
                return redirect(reverse('courseware', args=[course.id.to_deprecated_string()]))
            raise Http404

        if course_has_entrance_exam(course):
            # Message should not appear outside the context of entrance exam subsection.
            # if section is none then we don't need to show message on welcome back screen also.
            if getattr(chapter_module, 'is_entrance_exam', False) and section is not None:
                context['entrance_exam_current_score'] = get_entrance_exam_score(request, course)
                context['entrance_exam_passed'] = user_has_passed_entrance_exam(request, course)

        if section is not None:
            section_descriptor = chapter_descriptor.get_child_by(lambda m: m.location.name == section)

            if section_descriptor is None:
                # Specifically asked-for section doesn't exist
                if masquerade and masquerade.role == 'student':  # don't 404 if staff is masquerading as student
                    log.debug('staff masquerading as student: no section %s', section)
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
            field_data_cache.add_descriptor_descendents(
                section_descriptor, depth=None
            )

            section_module = get_module_for_descriptor(
                user,
                request,
                section_descriptor,
                field_data_cache,
                course_key,
                position,
                course=course
            )

            if section_module is None:
                # User may be trying to be clever and access something
                # they don't have access to.
                raise Http404

            # Save where we are in the chapter.
            save_child_position(chapter_module, section)
            section_render_context = {'activate_block_id': request.GET.get('activate_block_id')}
            context['fragment'] = section_module.render(STUDENT_VIEW, section_render_context)
            context['section_title'] = section_descriptor.display_name_with_default_escaped
        else:
            prev_section = get_current_child(chapter_module)
            if prev_section is None:
                # Something went wrong -- perhaps this chapter has no sections visible to the user.
                # Clearing out the last-visited state and showing "first-time" view by redirecting
                # to courseware.
                course_module.position = None
                course_module.save()
                return redirect(reverse('courseware', args=[course.id.to_deprecated_string()]))
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
                u"Error in index view: user=%s, effective_user=%s, course=%s, chapter=%s section=%s position=%s",
                request.user, user, course, chapter, section, position
            )
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
@ensure_valid_course_key
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
            u"Multiple items found with id: %s in course_id: %s. Referer: %s. Using first: %s",
            module_id,
            course_id,
            request.META.get("HTTP_REFERER", ""),
            items[0].location.to_deprecated_string()
        )

    return jump_to(request, course_id, items[0].location.to_deprecated_string())


@ensure_csrf_cookie
def jump_to(_request, course_id, location):
    """
    Show the page that contains a specific location.

    If the location is invalid or not in any class, return a 404.

    Otherwise, delegates to the index view to figure out whether this user
    has access, and what they should see.
    """
    try:
        course_key = CourseKey.from_string(course_id)
        usage_key = UsageKey.from_string(location).replace(course_key=course_key)
    except InvalidKeyError:
        raise Http404(u"Invalid course_key or usage_key")
    try:
        redirect_url = get_redirect_url(course_key, usage_key)
    except ItemNotFoundError:
        raise Http404(u"No data at this location: {0}".format(usage_key))
    except NoPathToItem:
        raise Http404(u"This location is not in any class: {0}".format(usage_key))

    return redirect(redirect_url)


@ensure_csrf_cookie
@ensure_valid_course_key
def course_info(request, course_id):
    """
    Display the course's info.html, or 404 if there is no such course.

    Assumes the course_id is in a valid format.
    """
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    with modulestore().bulk_operations(course_key):
        course = get_course_by_id(course_key, depth=2)
        access_response = has_access(request.user, 'load', course, course_key)

        if not access_response:

            # The user doesn't have access to the course. If they're
            # denied permission due to the course not being live yet,
            # redirect to the dashboard page.
            if isinstance(access_response, StartDateError):
                start_date = strftime_localized(course.start, 'SHORT_DATE')
                params = urllib.urlencode({'notlive': start_date})
                return redirect('{0}?{1}'.format(reverse('dashboard'), params))
            # Otherwise, give a 404 to avoid leaking info about access
            # control.
            raise Http404("Course not found.")

        staff_access = has_access(request.user, 'staff', course)
        masquerade, user = setup_masquerade(request, course_key, staff_access, reset_masquerade_data=True)

        # if user is not enrolled in a course then app will show enroll/get register link inside course info page.
        show_enroll_banner = request.user.is_authenticated() and not CourseEnrollment.is_enrolled(user, course.id)
        if show_enroll_banner and hasattr(course_key, 'ccx'):
            # if course is CCX and user is not enrolled/registered then do not let him open course direct via link for
            # self registration. Because only CCX coach can register/enroll a student. If un-enrolled user try
            # to access CCX redirect him to dashboard.
            return redirect(reverse('dashboard'))

        # If the user needs to take an entrance exam to access this course, then we'll need
        # to send them to that specific course module before allowing them into other areas
        if user_must_complete_entrance_exam(request, user, course):
            return redirect(reverse('courseware', args=[unicode(course.id)]))

        # check to see if there is a required survey that must be taken before
        # the user can access the course.
        if request.user.is_authenticated() and survey.utils.must_answer_survey(course, user):
            return redirect(reverse('course_survey', args=[unicode(course.id)]))

        studio_url = get_studio_url(course, 'course_info')

        # link to where the student should go to enroll in the course:
        # about page if there is not marketing site, SITE_NAME if there is
        url_to_enroll = reverse(course_about, args=[course_id])
        if settings.FEATURES.get('ENABLE_MKTG_SITE'):
            url_to_enroll = marketing_link('COURSES')

        context = {
            'request': request,
            'masquerade_user': user,
            'course_id': course_key.to_deprecated_string(),
            'cache': None,
            'course': course,
            'staff_access': staff_access,
            'masquerade': masquerade,
            'studio_url': studio_url,
            'show_enroll_banner': show_enroll_banner,
            'url_to_enroll': url_to_enroll,
        }

        # Get the URL of the user's last position in order to display the 'where you were last' message
        context['last_accessed_courseware_url'] = None
        if SelfPacedConfiguration.current().enable_course_home_improvements:
            context['last_accessed_courseware_url'] = get_last_accessed_courseware(course, request)

        now = datetime.now(UTC())
        effective_start = _adjust_start_date_for_beta_testers(user, course, course_key)
        if not in_preview_mode() and staff_access and now < effective_start:
            # Disable student view button if user is staff and
            # course is not yet visible to students.
            context['disable_student_access'] = True

        return render_to_response('courseware/info.html', context)


def get_last_accessed_courseware(course, request):
    """
    Return the URL the courseware module that this request's user last
    accessed, or None if it cannot be found.
    """
    field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
        course.id, request.user, course, depth=2
    )
    course_module = get_module_for_descriptor(
        request.user, request, course, field_data_cache, course.id, course=course
    )
    chapter_module = get_current_child(course_module)
    if chapter_module is not None:
        section_module = get_current_child(chapter_module)
        if section_module is not None:
            url = reverse('courseware_section', kwargs={
                'course_id': unicode(course.id),
                'chapter': chapter_module.url_name,
                'section': section_module.url_name
            })
            return url
    return None


@ensure_csrf_cookie
@ensure_valid_course_key
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


@ensure_csrf_cookie
@ensure_valid_course_key
def syllabus(request, course_id):
    """
    Display the course's syllabus.html, or 404 if there is no such course.

    Assumes the course_id is in a valid format.
    """

    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)

    course = get_course_with_access(request.user, 'load', course_key)
    staff_access = bool(has_access(request.user, 'staff', course))

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


def get_cosmetic_display_price(course, registration_price):
    """
    Return Course Price as a string preceded by correct currency, or 'Free'
    """
    currency_symbol = settings.PAID_COURSE_REGISTRATION_CURRENCY[1]

    price = course.cosmetic_display_price
    if registration_price > 0:
        price = registration_price

    if price:
        # Translators: This will look like '$50', where {currency_symbol} is a symbol such as '$' and {price} is a
        # numerical amount in that currency. Adjust this display as needed for your language.
        return _("{currency_symbol}{price}").format(currency_symbol=currency_symbol, price=price)
    else:
        # Translators: This refers to the cost of the course. In this case, the course costs nothing so it is free.
        return _('Free')


@ensure_csrf_cookie
@cache_if_anonymous()
def course_about(request, course_id):
    """
    Display the course's about page.

    Assumes the course_id is in a valid format.
    """

    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)

    if hasattr(course_key, 'ccx'):
        # if un-enrolled/non-registered user try to access CCX (direct for registration)
        # then do not show him about page to avoid self registration.
        # Note: About page will only be shown to user who is not register. So that he can register. But for
        # CCX only CCX coach can enroll students.
        return redirect(reverse('dashboard'))

    with modulestore().bulk_operations(course_key):
        permission = get_permission_for_course_about()
        course = get_course_with_access(request.user, permission, course_key)

        if microsite.get_value('ENABLE_MKTG_SITE', settings.FEATURES.get('ENABLE_MKTG_SITE', False)):
            return redirect(reverse('info', args=[course.id.to_deprecated_string()]))

        registered = registered_for_course(course, request.user)
        regularly_registered = (
            registered
            and
            UserProfile.has_registered(request.user)
        )

        staff_access = bool(has_access(request.user, 'staff', course))
        studio_url = get_studio_url(course, 'settings/details')

        if has_access(request.user, 'load', course):
            course_target = reverse('info', args=[course.id.to_deprecated_string()])
        else:
            course_target = reverse('about_course', args=[course.id.to_deprecated_string()])

        show_courseware_link = bool(
            (
                has_access(request.user, 'load', course)
                and has_access(request.user, 'view_courseware_with_prerequisites', course)
            )
            or settings.FEATURES.get('ENABLE_LMS_MIGRATION')
        )

        # Note: this is a flow for payment for course registration, not the Verified Certificate flow.
        registration_price = 0
        in_cart = False
        reg_then_add_to_cart_link = ""

        _is_shopping_cart_enabled = is_shopping_cart_enabled()
        if _is_shopping_cart_enabled:
            registration_price = CourseMode.min_course_price_for_currency(course_key,
                                                                          settings.PAID_COURSE_REGISTRATION_CURRENCY[0])
            if request.user.is_authenticated():
                cart = shoppingcart.models.Order.get_cart_for_user(request.user)
                in_cart = shoppingcart.models.PaidCourseRegistration.contained_in_order(cart, course_key) or \
                    shoppingcart.models.CourseRegCodeItem.contained_in_order(cart, course_key)

            reg_then_add_to_cart_link = "{reg_url}?course_id={course_id}&enrollment_action=add_to_cart".format(
                reg_url=reverse('register_user'), course_id=urllib.quote(str(course_id)))

        course_price = get_cosmetic_display_price(course, registration_price)
        can_add_course_to_cart = _is_shopping_cart_enabled and registration_price

        # only allow course sneak peek if
        # 1) within enrollment period
        # 2) course specifies it's okay
        # 3) request.user is not a registered user.
        sneakpeek_allowed = (has_access(request.user, 'within_enrollment_period', course) and
                             CoursePreference.course_allows_nonregistered_access(course_key) and
                             not UserProfile.has_registered(request.user))

        # Used to provide context to message to student if enrollment not allowed
        can_enroll = bool(has_access(request.user, 'enroll', course))
        invitation_only = course.invitation_only
        is_course_full = CourseEnrollment.objects.is_course_full(course)

        # Register button should be disabled if one of the following is true:
        # - Student is already registered for course
        # - Course is already full
        # - Student cannot enroll in course
        # active_reg_button = not(registered or is_course_full or not can_enroll)
        active_reg_button = not(regularly_registered or is_course_full or not can_enroll)

        is_shib_course = uses_shib(course)

        # get prerequisite courses display names
        pre_requisite_courses = get_prerequisite_courses_display(course)

        # Overview
        overview = CourseOverview.get_from_id(course.id)

        return render_to_response('courseware/course_about.html', {
            'course': course,
            'staff_access': staff_access,
            'studio_url': studio_url,
            'registered': registered,
            'course_target': course_target,
            'is_cosmetic_price_enabled': settings.FEATURES.get('ENABLE_COSMETIC_DISPLAY_PRICE'),
            'course_price': course_price,
            'in_cart': in_cart,
            'reg_then_add_to_cart_link': reg_then_add_to_cart_link,
            'show_courseware_link': show_courseware_link,
            'is_course_full': is_course_full,
            'can_enroll': can_enroll,
            'invitation_only': invitation_only,
            'active_reg_button': active_reg_button,
            'is_shib_course': is_shib_course,
            # We do not want to display the internal courseware header, which is used when the course is found in the
            # context. This value is therefor explicitly set to render the appropriate header.
            'disable_courseware_header': True,
            'can_add_course_to_cart': can_add_course_to_cart,
            'cart_link': reverse('shoppingcart.views.show_cart'),
            'pre_requisite_courses': pre_requisite_courses,
            'regularly_registered': regularly_registered,
            'sneakpeek_allowed': sneakpeek_allowed,
            'course_image_urls': overview.image_urls,
        })


@transaction.non_atomic_requests
@login_required
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@ensure_valid_course_key
def progress(request, course_id, student_id=None):
    """ Display the progress page. """

    course_key = CourseKey.from_string(course_id)

    with modulestore().bulk_operations(course_key):
        return _progress(request, course_key, student_id)


def _progress(request, course_key, student_id):
    """
    Unwrapped version of "progress".

    User progress. We show the grade bar and every problem score.

    Course staff are allowed to see the progress of students in their class.
    """
    course = get_course_with_access(request.user, 'load', course_key, depth=None, check_if_enrolled=True)

    # check to see if there is a required survey that must be taken before
    # the user can access the course.
    if survey.utils.must_answer_survey(course, request.user):
        return redirect(reverse('course_survey', args=[unicode(course.id)]))

    staff_access = bool(has_access(request.user, 'staff', course))
    try:
        coach_access = has_ccx_coach_role(request.user, course_key)
    except CCXLocatorValidationException:
        coach_access = False

    has_access_on_students_profiles = staff_access or coach_access

    if student_id is None or student_id == request.user.id:
        # always allowed to see your own profile
        student = request.user
    else:
        # Requesting access to a different student's profile
        if not has_access_on_students_profiles:
            raise Http404
        try:
            student = User.objects.get(id=student_id)
        # Check for ValueError if 'student_id' cannot be converted to integer.
        except (ValueError, User.DoesNotExist):
            raise Http404

    # NOTE: To make sure impersonation by instructor works, use
    # student instead of request.user in the rest of the function.

    # The pre-fetching of groups is done to make auth checks not require an
    # additional DB lookup (this kills the Progress page in particular).
    student = User.objects.prefetch_related("groups").get(id=student.id)

    with outer_atomic():
        field_data_cache = grades.field_data_cache_for_grading(course, student)
        scores_client = ScoresClient.from_field_data_cache(field_data_cache)

    courseware_summary = []
    if settings.FEATURES['ENABLE_PROGRESS_SUMMARY']:
        courseware_summary = grades.progress_summary(
            student, request, course, field_data_cache=field_data_cache, scores_client=scores_client
        )
    grade_summary = grades.grade(
        student, request, course, field_data_cache=field_data_cache, scores_client=scores_client
    )
    studio_url = get_studio_url(course, 'settings/grading')

    if courseware_summary is None:
        #This means the student didn't have access to the course (which the instructor requested)
        raise Http404

    # checking certificate generation configuration
    show_generate_cert_btn = certs_api.cert_generation_enabled(course_key)

    context = {
        'course': course,
        'courseware_summary': courseware_summary,
        'studio_url': studio_url,
        'grade_summary': grade_summary,
        'staff_access': staff_access,
        'student': student,
        'passed': is_course_passed(course, grade_summary),
        'show_generate_cert_btn': show_generate_cert_btn,
        'credit_course_requirements': _credit_course_requirements(course_key, student),
    }

    if show_generate_cert_btn:
        cert_status = certs_api.certificate_downloadable_status(student, course_key)
        context.update(cert_status)
        # showing the certificate web view button if feature flags are enabled.
        if certs_api.has_html_certificates_enabled(course_key, course):
            if certs_api.get_active_web_certificate(course) is not None:
                context.update({
                    'show_cert_web_view': True,
                    'cert_web_view_url': certs_api.get_certificate_url(course_id=course_key, uuid=cert_status['uuid']),
                })
            else:
                context.update({
                    'is_downloadable': False,
                    'is_generating': True,
                    'download_url': None
                })

    with outer_atomic():
        response = render_to_response('courseware/progress.html', context)

    return response


def _credit_course_requirements(course_key, student):
    """Return information about which credit requirements a user has satisfied.

    Arguments:
        course_key (CourseKey): Identifier for the course.
        student (User): Currently logged in user.

    Returns: dict if the credit eligibility enabled and it is a credit course
    and the user is enrolled in either verified or credit mode, and None otherwise.

    """
    # If credit eligibility is not enabled or this is not a credit course,
    # short-circuit and return `None`.  This indicates that credit requirements
    # should NOT be displayed on the progress page.
    if not (settings.FEATURES.get("ENABLE_CREDIT_ELIGIBILITY", False) and is_credit_course(course_key)):
        return None

    # If student is enrolled not enrolled in verified or credit mode,
    # short-circuit and return None. This indicates that
    # credit requirements should NOT be displayed on the progress page.
    enrollment = CourseEnrollment.get_enrollment(student, course_key)
    if enrollment.mode not in REQUIREMENTS_DISPLAY_MODES:
        return None

    # Credit requirement statuses for which user does not remain eligible to get credit.
    non_eligible_statuses = ['failed', 'declined']

    # Retrieve the status of the user for each eligibility requirement in the course.
    # For each requirement, the user's status is either "satisfied", "failed", or None.
    # In this context, `None` means that we don't know the user's status, either because
    # the user hasn't done something (for example, submitting photos for verification)
    # or we're waiting on more information (for example, a response from the photo
    # verification service).
    requirement_statuses = get_credit_requirement_status(course_key, student.username)

    # If the user has been marked as "eligible", then they are *always* eligible
    # unless someone manually intervenes.  This could lead to some strange behavior
    # if the requirements change post-launch.  For example, if the user was marked as eligible
    # for credit, then a new requirement was added, the user will see that they're eligible
    # AND that one of the requirements is still pending.
    # We're assuming here that (a) we can mitigate this by properly training course teams,
    # and (b) it's a better user experience to allow students who were at one time
    # marked as eligible to continue to be eligible.
    # If we need to, we can always manually move students back to ineligible by
    # deleting CreditEligibility records in the database.
    if is_user_eligible_for_credit(student.username, course_key):
        eligibility_status = "eligible"

    # If the user has *failed* any requirements (for example, if a photo verification is denied),
    # then the user is NOT eligible for credit.
    elif any(requirement['status'] in non_eligible_statuses for requirement in requirement_statuses):
        eligibility_status = "not_eligible"

    # Otherwise, the user may be eligible for credit, but the user has not
    # yet completed all the requirements.
    else:
        eligibility_status = "partial_eligible"

    return {
        'eligibility_status': eligibility_status,
        'requirements': requirement_statuses,
    }


@login_required
@ensure_valid_course_key
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

    course = get_course_overview_with_access(request.user, 'load', course_key)
    staff_access = bool(has_access(request.user, 'staff', course))

    # Permission Denied if they don't have staff access and are trying to see
    # somebody else's submission history.
    if (student_username != request.user.username) and (not staff_access):
        raise PermissionDenied

    user_state_client = DjangoXBlockUserStateClient()
    try:
        history_entries = list(user_state_client.get_history(student_username, usage_key))
    except DjangoXBlockUserStateClient.DoesNotExist:
        return HttpResponse(escape(_(u'User {username} has never accessed problem {location}').format(
            username=student_username,
            location=location
        )))

    # This is ugly, but until we have a proper submissions API that we can use to provide
    # the scores instead, it will have to do.
    scores = list(StudentModuleHistory.objects.filter(
        student_module__module_state_key=usage_key,
        student_module__student__username=student_username,
        student_module__course_id=course_key
    ).order_by('-id'))

    if len(scores) != len(history_entries):
        log.warning(
            "Mismatch when fetching scores for student "
            "history for course %s, user %s, xblock %s. "
            "%d scores were found, and %d history entries were found. "
            "Matching scores to history entries by date for display.",
            course_id,
            student_username,
            location,
            len(scores),
            len(history_entries),
        )
        scores_by_date = {
            score.created: score
            for score in scores
        }
        scores = [
            scores_by_date[history.updated]
            for history in history_entries
        ]

    context = {
        'history_entries': history_entries,
        'scores': scores,
        'username': student_username,
        'location': location,
        'course_id': course_key.to_deprecated_string()
    }

    return render_to_response('courseware/submission_history.html', context)


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
        request.user, request, loc, field_data_cache, static_asset_path=course.static_asset_path, course=course
    )

    logging.debug('course_module = %s', tab_module)

    html = ''
    if tab_module is not None:
        try:
            html = tab_module.render(STUDENT_VIEW).content
        except Exception:  # pylint: disable=broad-except
            html = render_to_string('courseware/error-message.html', None)
            log.exception(
                u"Error rendering course=%s, tab=%s", course, tab['url_slug']
            )

    return html


@require_GET
@ensure_valid_course_key
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
            course_key,
            course=course
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


def get_analytics_answer_dist(request):
    """
    Calls the the analytics answer distribution api client. Retrieves answer distribution data for the in-line
    analytics display.

    Arguments:
        request (django request object):  the HTTP request object that triggered this view function

    Returns:
        (django response object):  JSON response:
            500 if error occurred,
            404 if api client returns no data,
            otherwise 200 with JSON body.
    """
    all_data = json.loads(request.body)
    module_id = all_data['module_id']
    question_types_by_part = all_data['question_types_by_part']
    num_options_by_part = all_data['num_options_by_part']
    course_key = SlashSeparatedCourseKey.from_string(all_data['course_id'])

    # Construct an error message
    zendesk_url = getattr(settings, 'ZENDESK_URL')
    if zendesk_url:
        zendesk_url = '<a href=\"' + zendesk_url + '/hc/en-us/requests/new\">'
        error_message = _("A problem has occurred retrieving the data, to report the problem click "
                          "{zendesk_url}here{tag}").format(zendesk_url=zendesk_url, tag='</a>')
    else:
        error_message = _('A problem has occurred retrieving the data.')

    # Check user is enrolled as a staff member of this course
    try:
        course = get_course_with_access(request.user, 'staff', course_key, depth=None)
    except Http404:
        return HttpResponseServerError(error_message)

    having_access = has_access(request.user, 'staff', course)
    url = getattr(settings, 'ANALYTICS_DATA_URL')
    auth_token = getattr(settings, 'ANALYTICS_DATA_TOKEN')

    if not having_access or not url:
        return HttpResponseServerError(error_message)

    client = Client(base_url=url, auth_token=auth_token)
    module = client.modules(course.id, module_id)

    try:
        data = module.answer_distribution()
    except NotFoundError:
        return HttpResponseNotFound(_('There are no student answers for this problem yet; please try again later.'))
    except InvalidRequestError:
        return HttpResponseServerError(error_message)
    except TimeoutError:
        return HttpResponseServerError(error_message)

    return process_analytics_answer_dist(data, question_types_by_part, num_options_by_part)


def process_analytics_answer_dist(data, question_types_by_part, num_options_by_part):
    """
    Aggregates the analytics answer dist data.
    From the data, gets the date/time the data was last updated and reformats to the client TZ.

    Arguments:
        data: response from the analytics api
        question_types_by_part: dict of question types
        num_options_by_part: dict of number of options by question

    Returns:
        A json payload of:
          - data by part: an array of dicts of {value_id, correct, count} for each part_id
          - count by part: an array of dicts of {totalFirstAttemptCount,
                                                 totalFirstCorrectCount,
                                                 totalFirstIncorrectCount,
                                                 totalLastAttemptCount,
                                                 totalLastCorrectCount,
                                                 totalLastIncorrectCount} for each part_id
          - last updated: string
     """

    # Each element in count_by_part is a dict of totalAttemptCount, totalCorrectCount, totalIncorrectCount
    count_by_part = {}

    # Each element in data_by_part is an array of dicts of {value_id, correct, count}
    data_by_part = {}

    # For errors discovered during analytics data processing use message_by_part
    message_by_part = {}

    # Count rows returned for each part for integrity check
    num_rows_by_part = {}

    # List of part_ids to check for inconsistencies.
    part_id_set = set([])
    for data_dict in data:
        part_id_set.add(data_dict['part_id'])

    for item in data:
        part_id = item['part_id']

        num_rows_by_part[part_id] = num_rows_by_part.get(part_id, 0) + 1

        # If we detect an issue with the data, set error message and continue
        if _issue_with_data(item,
                            part_id,
                            message_by_part,
                            question_types_by_part,
                            num_options_by_part,
                            num_rows_by_part,
                            part_id_set):
            continue

        # Add count to appropriate aggregates
        count_dict = count_by_part.get(part_id, {
            'totalFirstAttemptCount': 0,
            'totalFirstCorrectCount': 0,
            'totalFirstIncorrectCount': 0,
            'totalLastAttemptCount': 0,
            'totalLastCorrectCount': 0,
            'totalLastIncorrectCount': 0,
        })
        count_dict['totalFirstAttemptCount'] = count_dict.get('totalFirstAttemptCount') + item['first_response_count']
        count_dict['totalLastAttemptCount'] = count_dict.get('totalLastAttemptCount') + item['last_response_count']
        if item['correct']:
            count_dict['totalFirstCorrectCount'] = count_dict.get('totalFirstCorrectCount') + item['first_response_count']
            count_dict['totalLastCorrectCount'] = count_dict.get('totalLastCorrectCount') + item['last_response_count']
        else:
            count_dict['totalFirstIncorrectCount'] = count_dict.get('totalFirstIncorrectCount') + item['first_response_count']
            count_dict['totalLastIncorrectCount'] = count_dict.get('totalLastIncorrectCount') + item['last_response_count']

        count_by_part[part_id] = count_dict

        # Add this item's data to the data for this part_id
        part_dict = {}
        part_dict['value_id'] = item['value_id']
        part_dict['correct'] = item['correct']
        part_dict['first_count'] = item['first_response_count']
        part_dict['last_count'] = item['last_response_count']

        data_by_part[part_id] = data_by_part.get(part_id, []) + [part_dict]

    # Determine the last updated date, convert to tz from settings and format
    created_date = data[0]['created']
    obj_date = datetime.strptime(created_date, '%Y-%m-%dT%H%M%S')
    obj_date = timezone('UTC').localize(obj_date)
    formatted_date_string = get_time_display(obj_date, None, coerce_tz=settings.TIME_ZONE_DISPLAYED_FOR_DEADLINES)

    response_payload = {
        'data_by_part': data_by_part,
        'count_by_part': count_by_part,
        'message_by_part': message_by_part,
        'last_update_date': formatted_date_string,
    }
    return JsonResponse(response_payload)


@login_required
def course_survey(request, course_id):
    """
    URL endpoint to present a survey that is associated with a course_id
    Note that the actual implementation of course survey is handled in the
    views.py file in the Survey Djangoapp
    """

    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    course = get_course_with_access(request.user, 'load', course_key)

    redirect_url = reverse('info', args=[course_id])

    # if there is no Survey associated with this course,
    # then redirect to the course instead
    if not course.course_survey_name:
        return redirect(redirect_url)

    return survey.views.view_student_survey(
        request.user,
        course.course_survey_name,
        course=course,
        redirect_url=redirect_url,
        is_required=course.course_survey_required,
    )


def _issue_with_data(item, part_id, message_by_part, question_types_by_part, num_options_by_part, num_rows_by_part, part_id_set):
    """
    A function where issues with the data returned by the analytics API are detected
    and an appropriate message formulated.

    Arguments:
        item: current row returned by the analytics API
        part_id: the part_id of the current row
        message_by_part: dictionary for storing error messages for parts
        question_types_by_part: dict of question types
        num_options_by_part: dict of number of options by question
        num_rows_by_part: dict of count of rows returned by API
        part_id_set: set of part_ids

    Returns:
        True: if an error was detected
        False: if no error was detected
    """

    # Data sanity check: if there is a part_id that is not a key in question_types_by_part
    # then there's an inconsistency between the problem definition and the analytics data.
    for part in part_id_set:
        if part not in question_types_by_part:
            message = _('The analytics cannot be displayed as there is an inconsistency in the data.')
            message_by_part[part_id] = message
            return True

    # Check variant (randomization) and if set, generate an error message
    if item['variant']:
        message = _('The analytics cannot be displayed for this question as randomization was set at one time.')
        message_by_part[part_id] = message
        return True

    # Check number of rows returned for radio question is consistent with definition
    if question_types_by_part[part_id] == 'radio' and num_rows_by_part[part_id] > num_options_by_part[part_id]:
        message = _('The analytics cannot be displayed for this question as the number of rows returned did not match '
                    'the question definition.')
        message_by_part[part_id] = message
        return True

    # Check number of rows returned for checkbox question is consistent with definition
    if question_types_by_part[part_id] == 'checkbox' and num_rows_by_part[part_id] > pow(2,
                                                                                         num_options_by_part[part_id]):
        message = _('The analytics cannot be displayed for this question as the number of rows returned did not match '
                    'the question definition.')
        message_by_part[part_id] = message
        return True

    return False


def is_course_passed(course, grade_summary=None, student=None, request=None):
    """
    check user's course passing status. return True if passed

    Arguments:
        course : course object
        grade_summary (dict) : contains student grade details.
        student : user object
        request (HttpRequest)

    Returns:
        returns bool value
    """
    nonzero_cutoffs = [cutoff for cutoff in course.grade_cutoffs.values() if cutoff > 0]
    success_cutoff = min(nonzero_cutoffs) if nonzero_cutoffs else None

    if grade_summary is None:
        grade_summary = grades.grade(student, request, course)

    return success_cutoff and grade_summary['percent'] >= success_cutoff


# Grades can potentially be written - if so, let grading manage the transaction.
@transaction.non_atomic_requests
@require_POST
def generate_user_cert(request, course_id):
    """Start generating a new certificate for the user.

    Certificate generation is allowed if:
    * The user has passed the course, and
    * The user does not already have a pending/completed certificate.

    Note that if an error occurs during certificate generation
    (for example, if the queue is down), then we simply mark the
    certificate generation task status as "error" and re-run
    the task with a management command.  To students, the certificate
    will appear to be "generating" until it is re-run.

    Args:
        request (HttpRequest): The POST request to this view.
        course_id (unicode): The identifier for the course.

    Returns:
        HttpResponse: 200 on success, 400 if a new certificate cannot be generated.

    """

    if not request.user.is_authenticated():
        log.info(u"Anon user trying to generate certificate for %s", course_id)
        return HttpResponseBadRequest(
            _('You must be signed in to {platform_name} to create a certificate.').format(
                platform_name=settings.PLATFORM_NAME
            )
        )

    student = request.user
    course_key = CourseKey.from_string(course_id)

    course = modulestore().get_course(course_key, depth=2)
    if not course:
        return HttpResponseBadRequest(_("Course is not valid"))

    if not is_course_passed(course, None, student, request):
        return HttpResponseBadRequest(_("Your certificate will be available when you pass the course."))

    certificate_status = certs_api.certificate_downloadable_status(student, course.id)

    if certificate_status["is_downloadable"]:
        return HttpResponseBadRequest(_("Certificate has already been created."))
    elif certificate_status["is_generating"]:
        return HttpResponseBadRequest(_("Certificate is being created."))
    else:
        # If the certificate is not already in-process or completed,
        # then create a new certificate generation task.
        # If the certificate cannot be added to the queue, this will
        # mark the certificate with "error" status, so it can be re-run
        # with a management command.  From the user's perspective,
        # it will appear that the certificate task was submitted successfully.
        certs_api.generate_user_certificates(student, course.id, course=course, generation_mode='self')
        _track_successful_certificate_generation(student.id, course.id)
        return HttpResponse()


def _track_successful_certificate_generation(user_id, course_id):  # pylint: disable=invalid-name
    """
    Track a successful certificate generation event.

    Arguments:
        user_id (str): The ID of the user generting the certificate.
        course_id (CourseKey): Identifier for the course.
    Returns:
        None

    """
    if settings.LMS_SEGMENT_KEY:
        event_name = 'edx.bi.user.certificate.generate'
        tracking_context = tracker.get_tracker().resolve_context()

        analytics.track(
            user_id,
            event_name,
            {
                'category': 'certificates',
                'label': unicode(course_id)
            },
            context={
                'ip': tracking_context.get('ip'),
                'Google Analytics': {
                    'clientId': tracking_context.get('client_id')
                }
            }
        )


@require_http_methods(["GET", "POST"])
def render_xblock(request, usage_key_string, check_if_enrolled=True):
    """
    Returns an HttpResponse with HTML content for the xBlock with the given usage_key.
    The returned HTML is a chromeless rendering of the xBlock (excluding content of the containing courseware).
    """
    usage_key = UsageKey.from_string(usage_key_string)
    usage_key = usage_key.replace(course_key=modulestore().fill_in_run(usage_key.course_key))
    course_key = usage_key.course_key

    requested_view = request.GET.get('view', 'student_view')
    if requested_view != 'student_view':
        return HttpResponseBadRequest("Rendering of the xblock view '{}' is not supported.".format(requested_view))

    with modulestore().bulk_operations(course_key):
        # verify the user has access to the course, including enrollment check
        try:
            course = get_course_with_access(request.user, 'load', course_key, check_if_enrolled=check_if_enrolled)
        except UserNotEnrolled:
            raise Http404("Course not found.")

        # get the block, which verifies whether the user has access to the block.
        block, _ = get_module_by_usage_id(
            request, unicode(course_key), unicode(usage_key), disable_staff_debug_info=True, course=course
        )

        context = {
            'fragment': block.render('student_view', context=request.GET),
            'course': course,
            'disable_accordion': True,
            'allow_iframing': True,
            'disable_header': True,
            'disable_footer': True,
            'disable_window_wrap': True,
            'disable_preview_menu': True,
            'staff_access': bool(has_access(request.user, 'staff', course)),
            'xqa_server': settings.FEATURES.get('XQA_SERVER', 'http://your_xqa_server.com'),
        }
        return render_to_response('courseware/courseware-chromeless.html', context)


# Translators: "percent_sign" is the symbol "%". "platform_name" is a
# string identifying the name of this installation, such as "edX".
FINANCIAL_ASSISTANCE_HEADER = _(
    '{platform_name} now offers financial assistance for learners who want to earn Verified Certificates but'
    ' who may not be able to pay the Verified Certificate fee. Eligible learners may receive up to 90{percent_sign} off'
    ' the Verified Certificate fee for a course.\nTo apply for financial assistance, enroll in the'
    ' audit track for a course that offers Verified Certificates, and then complete this application.'
    ' Note that you must complete a separate application for each course you take.\n We plan to use this'
    ' information to evaluate your application for financial assistance and to further develop our'
    ' financial assistance program.'
).format(
    percent_sign="%",
    platform_name=settings.PLATFORM_NAME
).split('\n')


FA_INCOME_LABEL = _('Annual Household Income')
FA_REASON_FOR_APPLYING_LABEL = _(
    'Tell us about your current financial situation. Why do you need assistance?'
)
FA_GOALS_LABEL = _(
    'Tell us about your learning or professional goals. How will a Verified Certificate in'
    ' this course help you achieve these goals?'
)
FA_EFFORT_LABEL = _(
    'Tell us about your plans for this course. What steps will you take to help you complete'
    ' the course work and receive a certificate?'
)
FA_SHORT_ANSWER_INSTRUCTIONS = _('Use between 250 and 500 words or so in your response.')


@login_required
def financial_assistance(_request):
    """Render the initial financial assistance page."""
    return render_to_response('financial-assistance/financial-assistance.html', {
        'header_text': FINANCIAL_ASSISTANCE_HEADER
    })


@login_required
@require_POST
def financial_assistance_request(request):
    """Submit a request for financial assistance to Zendesk."""
    try:
        data = json.loads(request.body)
        # Simple sanity check that the session belongs to the user
        # submitting an FA request
        username = data['username']
        if request.user.username != username:
            return HttpResponseForbidden()

        course_id = data['course']
        course = modulestore().get_course(CourseKey.from_string(course_id))
        legal_name = data['name']
        email = data['email']
        country = data['country']
        income = data['income']
        reason_for_applying = data['reason_for_applying']
        goals = data['goals']
        effort = data['effort']
        marketing_permission = data['mktg-permission']
        ip_address = get_ip(request)
    except ValueError:
        # Thrown if JSON parsing fails
        return HttpResponseBadRequest(u'Could not parse request JSON.')
    except InvalidKeyError:
        # Thrown if course key parsing fails
        return HttpResponseBadRequest(u'Could not parse request course key.')
    except KeyError as err:
        # Thrown if fields are missing
        return HttpResponseBadRequest(u'The field {} is required.'.format(err.message))

    zendesk_submitted = _record_feedback_in_zendesk(
        legal_name,
        email,
        u'Financial assistance request for learner {username} in course {course_name}'.format(
            username=username,
            course_name=course.display_name
        ),
        u'Financial Assistance Request',
        {'course_id': course_id},
        # Send the application as additional info on the ticket so
        # that it is not shown when support replies. This uses
        # OrderedDict so that information is presented in the right
        # order.
        OrderedDict((
            ('Username', username),
            ('Full Name', legal_name),
            ('Course ID', course_id),
            ('Annual Household Income', income),
            ('Country', country),
            ('Allowed for marketing purposes', 'Yes' if marketing_permission else 'No'),
            (FA_REASON_FOR_APPLYING_LABEL, '\n' + reason_for_applying + '\n\n'),
            (FA_GOALS_LABEL, '\n' + goals + '\n\n'),
            (FA_EFFORT_LABEL, '\n' + effort + '\n\n'),
            ('Client IP', ip_address),
        )),
        group_name='Financial Assistance',
        require_update=True
    )

    if not zendesk_submitted:
        # The call to Zendesk failed. The frontend will display a
        # message to the user.
        return HttpResponse(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return HttpResponse(status=status.HTTP_204_NO_CONTENT)


@login_required
def financial_assistance_form(request):
    """Render the financial assistance application form page."""
    user = request.user
    enrolled_courses = [
        {'name': enrollment.course_overview.display_name, 'value': unicode(enrollment.course_id)}
        for enrollment in CourseEnrollment.enrollments_for_user(user).order_by('-created')
        if CourseMode.objects.filter(
            Q(_expiration_datetime__isnull=True) | Q(_expiration_datetime__gt=datetime.now(UTC())),
            course_id=enrollment.course_id,
            mode_slug=CourseMode.VERIFIED
        ).exists()
        and enrollment.mode != CourseMode.VERIFIED
    ]
    return render_to_response('financial-assistance/apply.html', {
        'header_text': FINANCIAL_ASSISTANCE_HEADER,
        'student_faq_url': marketing_link('FAQ'),
        'dashboard_url': reverse('dashboard'),
        'account_settings_url': reverse('account_settings'),
        'platform_name': settings.PLATFORM_NAME,
        'user_details': {
            'email': user.email,
            'username': user.username,
            'name': user.profile.name,
            'country': str(user.profile.country.name),
        },
        'submit_url': reverse('submit_financial_assistance_request'),
        'fields': [
            {
                'name': 'course',
                'type': 'select',
                'label': _('Course'),
                'placeholder': '',
                'defaultValue': '',
                'required': True,
                'options': enrolled_courses,
                'instructions': _(
                    'Select the course for which you want to earn a verified certificate. If'
                    ' the course does not appear in the list, make sure that you have enrolled'
                    ' in the audit track for the course.'
                )
            },
            {
                'name': 'income',
                'type': 'text',
                'label': FA_INCOME_LABEL,
                'placeholder': _('income in US Dollars ($)'),
                'defaultValue': '',
                'required': True,
                'restrictions': {},
                'instructions': _('Specify your annual household income in US Dollars.')
            },
            {
                'name': 'reason_for_applying',
                'type': 'textarea',
                'label': FA_REASON_FOR_APPLYING_LABEL,
                'placeholder': '',
                'defaultValue': '',
                'required': True,
                'restrictions': {
                    'min_length': settings.FINANCIAL_ASSISTANCE_MIN_LENGTH,
                    'max_length': settings.FINANCIAL_ASSISTANCE_MAX_LENGTH
                },
                'instructions': FA_SHORT_ANSWER_INSTRUCTIONS
            },
            {
                'name': 'goals',
                'type': 'textarea',
                'label': FA_GOALS_LABEL,
                'placeholder': '',
                'defaultValue': '',
                'required': True,
                'restrictions': {
                    'min_length': settings.FINANCIAL_ASSISTANCE_MIN_LENGTH,
                    'max_length': settings.FINANCIAL_ASSISTANCE_MAX_LENGTH
                },
                'instructions': FA_SHORT_ANSWER_INSTRUCTIONS
            },
            {
                'name': 'effort',
                'type': 'textarea',
                'label': FA_EFFORT_LABEL,
                'placeholder': '',
                'defaultValue': '',
                'required': True,
                'restrictions': {
                    'min_length': settings.FINANCIAL_ASSISTANCE_MIN_LENGTH,
                    'max_length': settings.FINANCIAL_ASSISTANCE_MAX_LENGTH
                },
                'instructions': FA_SHORT_ANSWER_INSTRUCTIONS
            },
            {
                'placeholder': '',
                'name': 'mktg-permission',
                'label': _(
                    'I allow edX to use the information provided in this application '
                    '(except for financial information) for edX marketing purposes.'
                ),
                'defaultValue': '',
                'type': 'checkbox',
                'required': False,
                'instructions': '',
                'restrictions': {}
            }
        ],
    })
