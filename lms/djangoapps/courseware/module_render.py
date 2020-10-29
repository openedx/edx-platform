"""
Module rendering
"""


import hashlib
import json
import logging
import textwrap
from collections import OrderedDict
from functools import partial

import six
from completion import waffle as completion_waffle
from completion.models import BlockCompletion
from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import transaction
from django.http import Http404, HttpResponse, HttpResponseForbidden
from django.middleware.csrf import CsrfViewMiddleware
from django.template.context_processors import csrf
from django.urls import reverse
from django.utils.text import slugify
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.csrf import csrf_exempt
from edx_django_utils.cache import RequestCache
from edx_django_utils.monitoring import set_custom_attributes_for_course_key, set_monitoring_transaction_name
from edx_proctoring.api import get_attempt_status_summary
from edx_proctoring.services import ProctoringService
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_when.field_data import DateLookupFieldData
from eventtracking import tracker
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey, UsageKey
from requests.auth import HTTPBasicAuth
from rest_framework.decorators import api_view
from rest_framework.exceptions import APIException
from six import text_type
from web_fragments.fragment import Fragment
from xblock.core import XBlock
from xblock.django.request import django_to_webob_request, webob_to_django_response
from xblock.exceptions import NoSuchHandlerError, NoSuchViewError
from xblock.reference.plugins import FSService
from xblock.runtime import KvsFieldData

from common.djangoapps import static_replace
from capa.xqueue_interface import XQueueInterface
from lms.djangoapps.courseware.access import get_user_role, has_access
from lms.djangoapps.courseware.entrance_exams import user_can_skip_entrance_exam, user_has_passed_entrance_exam
from lms.djangoapps.courseware.masquerade import (
    MasqueradingKeyValueStore,
    filter_displayed_blocks,
    is_masquerading_as_specific_student,
    setup_masquerade
)
from lms.djangoapps.courseware.model_data import DjangoKeyValueStore, FieldDataCache
from common.djangoapps.edxmako.shortcuts import render_to_string
from lms.djangoapps.courseware.field_overrides import OverrideFieldData
from lms.djangoapps.courseware.services import UserStateService
from lms.djangoapps.grades.api import GradesUtilService
from lms.djangoapps.grades.api import signals as grades_signals
from lms.djangoapps.lms_xblock.field_data import LmsFieldData
from lms.djangoapps.lms_xblock.models import XBlockAsidesConfig
from lms.djangoapps.lms_xblock.runtime import LmsModuleSystem
from lms.djangoapps.verify_student.services import XBlockVerificationService
from openedx.core.djangoapps.bookmarks.services import BookmarksService
from openedx.core.djangoapps.crawlers.models import CrawlersConfig
from openedx.core.djangoapps.credit.services import CreditService
from openedx.core.djangoapps.util.user_utils import SystemUser
from openedx.core.djangolib.markup import HTML
from openedx.core.lib.api.authentication import BearerAuthenticationAllowInactiveUser
from openedx.core.lib.api.view_utils import view_auth_classes
from openedx.core.lib.gating.services import GatingService
from openedx.core.lib.license import wrap_with_license
from openedx.core.lib.url_utils import quote_slashes, unquote_slashes
from openedx.core.lib.xblock_utils import (
    add_staff_markup,
    get_aside_from_xblock,
    hash_resource,
    is_xblock_aside,
    replace_course_urls,
    replace_jump_to_id_urls,
    replace_static_urls
)
from openedx.core.lib.xblock_utils import request_token as xblock_request_token
from openedx.core.lib.xblock_utils import wrap_xblock
from openedx.features.course_duration_limits.access import course_expiration_wrapper
from openedx.features.discounts.utils import offer_banner_wrapper
from openedx.features.content_type_gating.services import ContentTypeGatingService
from common.djangoapps.student.models import anonymous_id_for_user, user_by_anonymous_id
from common.djangoapps.student.roles import CourseBetaTesterRole
from common.djangoapps.track import contexts
from common.djangoapps.util import milestones_helpers
from common.djangoapps.util.json_request import JsonResponse
from common.djangoapps.xblock_django.user_service import DjangoXBlockUserService
from xmodule.contentstore.django import contentstore
from xmodule.error_module import ErrorDescriptor, NonStaffErrorDescriptor
from xmodule.exceptions import NotFoundError, ProcessingError
from xmodule.lti_module import LTIModule
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError
from xmodule.util.sandboxing import can_execute_unsafe_code, get_python_lib_zip
from xmodule.x_module import XModuleDescriptor

log = logging.getLogger(__name__)

if settings.XQUEUE_INTERFACE.get('basic_auth') is not None:
    REQUESTS_AUTH = HTTPBasicAuth(*settings.XQUEUE_INTERFACE['basic_auth'])
else:
    REQUESTS_AUTH = None

XQUEUE_INTERFACE = XQueueInterface(
    settings.XQUEUE_INTERFACE['url'],
    settings.XQUEUE_INTERFACE['django_auth'],
    REQUESTS_AUTH,
)

# TODO: course_id and course_key are used interchangeably in this file, which is wrong.
# Some brave person should make the variable names consistently someday, but the code's
# coupled enough that it's kind of tricky--you've been warned!


class LmsModuleRenderError(Exception):
    """
    An exception class for exceptions thrown by module_render that don't fit well elsewhere
    """
    pass


def make_track_function(request):
    '''
    Make a tracking function that logs what happened.
    For use in ModuleSystem.
    '''
    from common.djangoapps.track import views as track_views

    def function(event_type, event):
        return track_views.server_track(request, event_type, event, page='x_module')
    return function


def toc_for_course(user, request, course, active_chapter, active_section, field_data_cache):
    '''
    Create a table of contents from the module store

    Return format:
    { 'chapters': [
            {'display_name': name, 'url_name': url_name, 'sections': SECTIONS, 'active': bool},
        ],
        'previous_of_active_section': {..},
        'next_of_active_section': {..}
    }

    where SECTIONS is a list
    [ {'display_name': name, 'url_name': url_name,
       'format': format, 'due': due, 'active' : bool, 'graded': bool}, ...]

    where previous_of_active_section and next_of_active_section have information on the
    next/previous sections of the active section.

    active is set for the section and chapter corresponding to the passed
    parameters, which are expected to be url_names of the chapter+section.
    Everything else comes from the xml, or defaults to "".

    chapters with name 'hidden' are skipped.

    NOTE: assumes that if we got this far, user has access to course.  Returns
    None if this is not the case.

    field_data_cache must include data from the course module and 2 levels of its descendants
    '''
    with modulestore().bulk_operations(course.id):
        course_module = get_module_for_descriptor(
            user, request, course, field_data_cache, course.id, course=course
        )
        if course_module is None:
            return None, None, None

        toc_chapters = list()
        chapters = course_module.get_display_items()

        # Check for content which needs to be completed
        # before the rest of the content is made available
        required_content = milestones_helpers.get_required_content(course.id, user)

        # The user may not actually have to complete the entrance exam, if one is required
        if user_can_skip_entrance_exam(user, course):
            required_content = [content for content in required_content if not content == course.entrance_exam_id]

        previous_of_active_section, next_of_active_section = None, None
        last_processed_section, last_processed_chapter = None, None
        found_active_section = False
        for chapter in chapters:
            # Only show required content, if there is required content
            # chapter.hide_from_toc is read-only (bool)
            # xss-lint: disable=python-deprecated-display-name
            display_id = slugify(chapter.display_name_with_default_escaped)
            local_hide_from_toc = False
            if required_content:
                if six.text_type(chapter.location) not in required_content:
                    local_hide_from_toc = True

            # Skip the current chapter if a hide flag is tripped
            if chapter.hide_from_toc or local_hide_from_toc:
                continue

            sections = list()
            for section in chapter.get_display_items():
                # skip the section if it is hidden from the user
                if section.hide_from_toc:
                    continue

                is_section_active = (chapter.url_name == active_chapter and section.url_name == active_section)
                if is_section_active:
                    found_active_section = True

                section_context = {
                    # xss-lint: disable=python-deprecated-display-name
                    'display_name': section.display_name_with_default_escaped,
                    'url_name': section.url_name,
                    'format': section.format if section.format is not None else '',
                    'due': section.due,
                    'active': is_section_active,
                    'graded': section.graded,
                }
                _add_timed_exam_info(user, course, section, section_context)

                # update next and previous of active section, if applicable
                if is_section_active:
                    if last_processed_section:
                        previous_of_active_section = last_processed_section.copy()
                        previous_of_active_section['chapter_url_name'] = last_processed_chapter.url_name
                elif found_active_section and not next_of_active_section:
                    next_of_active_section = section_context.copy()
                    next_of_active_section['chapter_url_name'] = chapter.url_name

                sections.append(section_context)
                last_processed_section = section_context
                last_processed_chapter = chapter

            toc_chapters.append({
                # xss-lint: disable=python-deprecated-display-name
                'display_name': chapter.display_name_with_default_escaped,
                'display_id': display_id,
                'url_name': chapter.url_name,
                'sections': sections,
                'active': chapter.url_name == active_chapter
            })
        return {
            'chapters': toc_chapters,
            'previous_of_active_section': previous_of_active_section,
            'next_of_active_section': next_of_active_section,
        }


def _add_timed_exam_info(user, course, section, section_context):
    """
    Add in rendering context if exam is a timed exam (which includes proctored)
    """
    section_is_time_limited = (
        getattr(section, 'is_time_limited', False) and
        settings.FEATURES.get('ENABLE_SPECIAL_EXAMS', False)
    )
    if section_is_time_limited:
        # call into edx_proctoring subsystem
        # to get relevant proctoring information regarding this
        # level of the courseware
        #
        # This will return None, if (user, course_id, content_id)
        # is not applicable
        timed_exam_attempt_context = None
        try:
            timed_exam_attempt_context = get_attempt_status_summary(
                user.id,
                six.text_type(course.id),
                six.text_type(section.location)
            )
        except Exception as ex:  # pylint: disable=broad-except
            # safety net in case something blows up in edx_proctoring
            # as this is just informational descriptions, it is better
            # to log and continue (which is safe) than to have it be an
            # unhandled exception
            log.exception(ex)

        if timed_exam_attempt_context:
            # yes, user has proctoring context about
            # this level of the courseware
            # so add to the accordion data context
            section_context.update({
                'proctoring': timed_exam_attempt_context,
            })


def get_module(user, request, usage_key, field_data_cache,
               position=None, log_if_not_found=True, wrap_xmodule_display=True,
               grade_bucket_type=None, depth=0,
               static_asset_path='', course=None, will_recheck_access=False):
    """
    Get an instance of the xmodule class identified by location,
    setting the state based on an existing StudentModule, or creating one if none
    exists.

    Arguments:
      - user                  : User for whom we're getting the module
      - request               : current django HTTPrequest.  Note: request.user isn't used for anything--all auth
                                and such works based on user.
      - usage_key             : A UsageKey object identifying the module to load
      - field_data_cache      : a FieldDataCache
      - position              : extra information from URL for user-specified
                                position within module
      - log_if_not_found      : If this is True, we log a debug message if we cannot find the requested xmodule.
      - wrap_xmodule_display  : If this is True, wrap the output display in a single div to allow for the
                                XModule javascript to be bound correctly
      - depth                 : number of levels of descendents to cache when loading this module.
                                None means cache all descendents
      - static_asset_path     : static asset path to use (overrides descriptor's value); needed
                                by get_course_info_section, because info section modules
                                do not have a course as the parent module, and thus do not
                                inherit this lms key value.
      - will_recheck_access   : If True, the caller commits to re-checking access on each child XBlock
                                before rendering the content in order to display access error messages
                                to the user.

    Returns: xmodule instance, or None if the user does not have access to the
    module.  If there's an error, will try to return an instance of ErrorModule
    if possible.  If not possible, return None.
    """
    try:
        descriptor = modulestore().get_item(usage_key, depth=depth)
        return get_module_for_descriptor(user, request, descriptor, field_data_cache, usage_key.course_key,
                                         position=position,
                                         wrap_xmodule_display=wrap_xmodule_display,
                                         grade_bucket_type=grade_bucket_type,
                                         static_asset_path=static_asset_path,
                                         course=course, will_recheck_access=will_recheck_access)
    except ItemNotFoundError:
        if log_if_not_found:
            log.debug("Error in get_module: ItemNotFoundError")
        return None

    except:  # pylint: disable=W0702
        # Something has gone terribly wrong, but still not letting it turn into a 500.
        log.exception("Error in get_module")
        return None


def display_access_messages(user, block, view, frag, context):  # pylint: disable=W0613
    """
    An XBlock wrapper that replaces the content fragment with a fragment or message determined by
    the has_access check.
    """
    blocked_prior_sibling = RequestCache('display_access_messages_prior_sibling')

    load_access = has_access(user, 'load', block, block.scope_ids.usage_id.course_key)
    if load_access:
        blocked_prior_sibling.delete(block.parent)
        return frag

    prior_sibling = blocked_prior_sibling.get_cached_response(block.parent)

    if prior_sibling.is_found and prior_sibling.value.error_code == load_access.error_code:
        return Fragment(u"")
    else:
        blocked_prior_sibling.set(block.parent, load_access)

    if load_access.user_fragment:
        msg_fragment = load_access.user_fragment
    elif load_access.user_message:
        msg_fragment = Fragment(textwrap.dedent(HTML(u"""\
            <div>{}</div>
        """).format(load_access.user_message)))
    else:
        msg_fragment = Fragment(u"")

    if load_access.developer_message and has_access(user, 'staff', block, block.scope_ids.usage_id.course_key):
        msg_fragment.content += textwrap.dedent(HTML(u"""\
            <div>{}</div>
        """).format(load_access.developer_message))

    return msg_fragment


def get_xqueue_callback_url_prefix(request):
    """
    Calculates default prefix based on request, but allows override via settings

    This is separated from get_module_for_descriptor so that it can be called
    by the LMS before submitting background tasks to run.  The xqueue callbacks
    should go back to the LMS, not to the worker.
    """
    prefix = '{proto}://{host}'.format(
        proto=request.META.get('HTTP_X_FORWARDED_PROTO', 'https' if request.is_secure() else 'http'),
        host=request.get_host()
    )
    return settings.XQUEUE_INTERFACE.get('callback_url', prefix)


# pylint: disable=too-many-statements
def get_module_for_descriptor(user, request, descriptor, field_data_cache, course_key,
                              position=None, wrap_xmodule_display=True, grade_bucket_type=None,
                              static_asset_path='', disable_staff_debug_info=False,
                              course=None, will_recheck_access=False):
    """
    Implements get_module, extracting out the request-specific functionality.

    disable_staff_debug_info : If this is True, exclude staff debug information in the rendering of the module.

    See get_module() docstring for further details.
    """
    track_function = make_track_function(request)
    xqueue_callback_url_prefix = get_xqueue_callback_url_prefix(request)

    user_location = getattr(request, 'session', {}).get('country_code')

    student_kvs = DjangoKeyValueStore(field_data_cache)
    if is_masquerading_as_specific_student(user, course_key):
        student_kvs = MasqueradingKeyValueStore(student_kvs, request.session)
    student_data = KvsFieldData(student_kvs)

    return get_module_for_descriptor_internal(
        user=user,
        descriptor=descriptor,
        student_data=student_data,
        course_id=course_key,
        track_function=track_function,
        xqueue_callback_url_prefix=xqueue_callback_url_prefix,
        position=position,
        wrap_xmodule_display=wrap_xmodule_display,
        grade_bucket_type=grade_bucket_type,
        static_asset_path=static_asset_path,
        user_location=user_location,
        request_token=xblock_request_token(request),
        disable_staff_debug_info=disable_staff_debug_info,
        course=course,
        will_recheck_access=will_recheck_access,
    )


def get_module_system_for_user(
        user,
        student_data,  # TODO
        # Arguments preceding this comment have user binding, those following don't
        descriptor,
        course_id,
        track_function,
        xqueue_callback_url_prefix,
        request_token,
        position=None,
        wrap_xmodule_display=True,
        grade_bucket_type=None,
        static_asset_path='',
        user_location=None,
        disable_staff_debug_info=False,
        course=None,
        will_recheck_access=False,
):
    """
    Helper function that returns a module system and student_data bound to a user and a descriptor.

    The purpose of this function is to factor out everywhere a user is implicitly bound when creating a module,
    to allow an existing module to be re-bound to a user.  Most of the user bindings happen when creating the
    closures that feed the instantiation of ModuleSystem.

    The arguments fall into two categories: those that have explicit or implicit user binding, which are user
    and student_data, and those don't and are just present so that ModuleSystem can be instantiated, which
    are all the other arguments.  Ultimately, this isn't too different than how get_module_for_descriptor_internal
    was before refactoring.

    Arguments:
        see arguments for get_module()
        request_token (str): A token unique to the request use by xblock initialization

    Returns:
        (LmsModuleSystem, KvsFieldData):  (module system, student_data) bound to, primarily, the user and descriptor
    """

    def make_xqueue_callback(dispatch='score_update'):
        """
        Returns fully qualified callback URL for external queueing system
        """
        relative_xqueue_callback_url = reverse(
            'xqueue_callback',
            kwargs=dict(
                course_id=text_type(course_id),
                userid=str(user.id),
                mod_id=text_type(descriptor.location),
                dispatch=dispatch
            ),
        )
        return xqueue_callback_url_prefix + relative_xqueue_callback_url

    # Default queuename is course-specific and is derived from the course that
    #   contains the current module.
    # TODO: Queuename should be derived from 'course_settings.json' of each course
    xqueue_default_queuename = descriptor.location.org + '-' + descriptor.location.course

    xqueue = {
        'interface': XQUEUE_INTERFACE,
        'construct_callback': make_xqueue_callback,
        'default_queuename': xqueue_default_queuename.replace(' ', '_'),
        'waittime': settings.XQUEUE_WAITTIME_BETWEEN_REQUESTS
    }

    def inner_get_module(descriptor):
        """
        Delegate to get_module_for_descriptor_internal() with all values except `descriptor` set.

        Because it does an access check, it may return None.
        """
        # TODO: fix this so that make_xqueue_callback uses the descriptor passed into
        # inner_get_module, not the parent's callback.  Add it as an argument....
        return get_module_for_descriptor_internal(
            user=user,
            descriptor=descriptor,
            student_data=student_data,
            course_id=course_id,
            track_function=track_function,
            xqueue_callback_url_prefix=xqueue_callback_url_prefix,
            position=position,
            wrap_xmodule_display=wrap_xmodule_display,
            grade_bucket_type=grade_bucket_type,
            static_asset_path=static_asset_path,
            user_location=user_location,
            request_token=request_token,
            course=course,
            will_recheck_access=will_recheck_access,
        )

    def get_event_handler(event_type):
        """
        Return an appropriate function to handle the event.

        Returns None if no special processing is required.
        """
        handlers = {
            'grade': handle_grade_event,
        }
        if completion_waffle.waffle().is_enabled(completion_waffle.ENABLE_COMPLETION_TRACKING):
            handlers.update({
                'completion': handle_completion_event,
                'progress': handle_deprecated_progress_event,
            })
        return handlers.get(event_type)

    def publish(block, event_type, event):
        """
        A function that allows XModules to publish events.
        """
        handle_event = get_event_handler(event_type)
        if handle_event and not is_masquerading_as_specific_student(user, course_id):
            handle_event(block, event)
        else:
            context = contexts.course_context_from_course_id(course_id)
            if block.runtime.user_id:
                context['user_id'] = block.runtime.user_id
            context['asides'] = {}
            for aside in block.runtime.get_asides(block):
                if hasattr(aside, 'get_event_context'):
                    aside_event_info = aside.get_event_context(event_type, event)
                    if aside_event_info is not None:
                        context['asides'][aside.scope_ids.block_type] = aside_event_info
            with tracker.get_tracker().context(event_type, context):
                track_function(event_type, event)

    def handle_completion_event(block, event):
        """
        Submit a completion object for the block.
        """
        if not completion_waffle.waffle().is_enabled(completion_waffle.ENABLE_COMPLETION_TRACKING):
            raise Http404
        else:
            BlockCompletion.objects.submit_completion(
                user=user,
                block_key=block.scope_ids.usage_id,
                completion=event['completion'],
            )

    def handle_grade_event(block, event):
        """
        Submit a grade for the block.
        """
        if not user.is_anonymous:
            grades_signals.SCORE_PUBLISHED.send(
                sender=None,
                block=block,
                user=user,
                raw_earned=event['value'],
                raw_possible=event['max_value'],
                only_if_higher=event.get('only_if_higher'),
                score_deleted=event.get('score_deleted'),
                grader_response=event.get('grader_response')
            )

    def handle_deprecated_progress_event(block, event):
        """
        DEPRECATED: Submit a completion for the block represented by the
        progress event.

        This exists to support the legacy progress extension used by
        edx-solutions.  New XBlocks should not emit these events, but instead
        emit completion events directly.
        """
        if not completion_waffle.waffle().is_enabled(completion_waffle.ENABLE_COMPLETION_TRACKING):
            raise Http404
        else:
            requested_user_id = event.get('user_id', user.id)
            if requested_user_id != user.id:
                log.warning(u"{} tried to submit a completion on behalf of {}".format(user, requested_user_id))
                return

            # If blocks explicitly declare support for the new completion API,
            # we expect them to emit 'completion' events,
            # and we ignore the deprecated 'progress' events
            # in order to avoid duplicate work and possibly conflicting semantics.
            if not getattr(block, 'has_custom_completion', False):
                BlockCompletion.objects.submit_completion(
                    user=user,
                    block_key=block.scope_ids.usage_id,
                    completion=1.0,
                )

    def rebind_noauth_module_to_user(module, real_user):
        """
        A function that allows a module to get re-bound to a real user if it was previously bound to an AnonymousUser.

        Will only work within a module bound to an AnonymousUser, e.g. one that's instantiated by the noauth_handler.

        Arguments:
            module (any xblock type):  the module to rebind
            real_user (django.contrib.auth.models.User):  the user to bind to

        Returns:
            nothing (but the side effect is that module is re-bound to real_user)
        """
        if user.is_authenticated:
            err_msg = ("rebind_noauth_module_to_user can only be called from a module bound to "
                       "an anonymous user")
            log.error(err_msg)
            raise LmsModuleRenderError(err_msg)

        field_data_cache_real_user = FieldDataCache.cache_for_descriptor_descendents(
            course_id,
            real_user,
            module.descriptor,
            asides=XBlockAsidesConfig.possible_asides(),
        )
        student_data_real_user = KvsFieldData(DjangoKeyValueStore(field_data_cache_real_user))

        (inner_system, inner_student_data) = get_module_system_for_user(
            user=real_user,
            student_data=student_data_real_user,  # These have implicit user bindings, rest of args considered not to
            descriptor=module.descriptor,
            course_id=course_id,
            track_function=track_function,
            xqueue_callback_url_prefix=xqueue_callback_url_prefix,
            position=position,
            wrap_xmodule_display=wrap_xmodule_display,
            grade_bucket_type=grade_bucket_type,
            static_asset_path=static_asset_path,
            user_location=user_location,
            request_token=request_token,
            course=course,
            will_recheck_access=will_recheck_access,
        )

        module.descriptor.bind_for_student(
            inner_system,
            real_user.id,
            [
                partial(DateLookupFieldData, course_id=course_id, user=user),
                partial(OverrideFieldData.wrap, real_user, course),
                partial(LmsFieldData, student_data=inner_student_data),
            ],
        )

        module.descriptor.scope_ids = (
            module.descriptor.scope_ids._replace(user_id=real_user.id)
        )
        module.scope_ids = module.descriptor.scope_ids  # this is needed b/c NamedTuples are immutable
        # now bind the module to the new ModuleSystem instance and vice-versa
        module.runtime = inner_system
        inner_system.xmodule_instance = module

    # Build a list of wrapping functions that will be applied in order
    # to the Fragment content coming out of the xblocks that are about to be rendered.
    block_wrappers = []

    if is_masquerading_as_specific_student(user, course_id):
        block_wrappers.append(filter_displayed_blocks)

    if settings.FEATURES.get("LICENSING", False):
        block_wrappers.append(wrap_with_license)

    # Wrap the output display in a single div to allow for the XModule
    # javascript to be bound correctly
    if wrap_xmodule_display is True:
        block_wrappers.append(partial(
            wrap_xblock,
            'LmsRuntime',
            extra_data={'course-id': text_type(course_id)},
            usage_id_serializer=lambda usage_id: quote_slashes(text_type(usage_id)),
            request_token=request_token,
        ))

    # TODO (cpennington): When modules are shared between courses, the static
    # prefix is going to have to be specific to the module, not the directory
    # that the xml was loaded from

    # Rewrite urls beginning in /static to point to course-specific content
    block_wrappers.append(partial(
        replace_static_urls,
        getattr(descriptor, 'data_dir', None),
        course_id=course_id,
        static_asset_path=static_asset_path or descriptor.static_asset_path
    ))

    # Allow URLs of the form '/course/' refer to the root of multicourse directory
    #   hierarchy of this course
    block_wrappers.append(partial(replace_course_urls, course_id))

    # this will rewrite intra-courseware links (/jump_to_id/<id>). This format
    # is an improvement over the /course/... format for studio authored courses,
    # because it is agnostic to course-hierarchy.
    # NOTE: module_id is empty string here. The 'module_id' will get assigned in the replacement
    # function, we just need to specify something to get the reverse() to work.
    block_wrappers.append(partial(
        replace_jump_to_id_urls,
        course_id,
        reverse('jump_to_id', kwargs={'course_id': text_type(course_id), 'module_id': ''}),
    ))

    block_wrappers.append(partial(display_access_messages, user))
    block_wrappers.append(partial(course_expiration_wrapper, user))
    block_wrappers.append(partial(offer_banner_wrapper, user))

    if settings.FEATURES.get('DISPLAY_DEBUG_INFO_TO_STAFF'):
        if is_masquerading_as_specific_student(user, course_id):
            # When masquerading as a specific student, we want to show the debug button
            # unconditionally to enable resetting the state of the student we are masquerading as.
            # We already know the user has staff access when masquerading is active.
            staff_access = True
            # To figure out whether the user has instructor access, we temporarily remove the
            # masquerade_settings from the real_user.  With the masquerading settings in place,
            # the result would always be "False".
            masquerade_settings = user.real_user.masquerade_settings
            del user.real_user.masquerade_settings
            user.real_user.masquerade_settings = masquerade_settings
        else:
            staff_access = has_access(user, 'staff', descriptor, course_id)
        if staff_access:
            block_wrappers.append(partial(add_staff_markup, user, disable_staff_debug_info))

    # These modules store data using the anonymous_student_id as a key.
    # To prevent loss of data, we will continue to provide old modules with
    # the per-student anonymized id (as we have in the past),
    # while giving selected modules a per-course anonymized id.
    # As we have the time to manually test more modules, we can add to the list
    # of modules that get the per-course anonymized id.
    is_pure_xblock = isinstance(descriptor, XBlock) and not isinstance(descriptor, XModuleDescriptor)
    module_class = getattr(descriptor, 'module_class', None)
    is_lti_module = not is_pure_xblock and issubclass(module_class, LTIModule)
    if (is_pure_xblock and not getattr(descriptor, 'requires_per_student_anonymous_id', False)) or is_lti_module:
        anonymous_student_id = anonymous_id_for_user(user, course_id)
    else:
        anonymous_student_id = anonymous_id_for_user(user, None)

    field_data = DateLookupFieldData(descriptor._field_data, course_id, user)  # pylint: disable=protected-access
    field_data = LmsFieldData(field_data, student_data)

    user_is_staff = bool(has_access(user, u'staff', descriptor.location, course_id))

    system = LmsModuleSystem(
        track_function=track_function,
        render_template=render_to_string,
        static_url=settings.STATIC_URL,
        xqueue=xqueue,
        # TODO (cpennington): Figure out how to share info between systems
        filestore=descriptor.runtime.resources_fs,
        get_module=inner_get_module,
        user=user,
        debug=settings.DEBUG,
        hostname=settings.SITE_NAME,
        # TODO (cpennington): This should be removed when all html from
        # a module is coming through get_html and is therefore covered
        # by the replace_static_urls code below
        replace_urls=partial(
            static_replace.replace_static_urls,
            data_directory=getattr(descriptor, 'data_dir', None),
            course_id=course_id,
            static_asset_path=static_asset_path or descriptor.static_asset_path,
        ),
        replace_course_urls=partial(
            static_replace.replace_course_urls,
            course_key=course_id
        ),
        replace_jump_to_id_urls=partial(
            static_replace.replace_jump_to_id_urls,
            course_id=course_id,
            jump_to_id_base_url=reverse('jump_to_id', kwargs={'course_id': text_type(course_id), 'module_id': ''})
        ),
        node_path=settings.NODE_PATH,
        publish=publish,
        anonymous_student_id=anonymous_student_id,
        course_id=course_id,
        cache=cache,
        can_execute_unsafe_code=(lambda: can_execute_unsafe_code(course_id)),
        get_python_lib_zip=(lambda: get_python_lib_zip(contentstore, course_id)),
        # TODO: When we merge the descriptor and module systems, we can stop reaching into the mixologist (cpennington)
        mixins=descriptor.runtime.mixologist._mixins,  # pylint: disable=protected-access
        wrappers=block_wrappers,
        get_real_user=user_by_anonymous_id,
        services={
            'fs': FSService(),
            'field-data': field_data,
            'user': DjangoXBlockUserService(user, user_is_staff=user_is_staff),
            'verification': XBlockVerificationService(),
            'proctoring': ProctoringService(),
            'milestones': milestones_helpers.get_service(),
            'credit': CreditService(),
            'bookmarks': BookmarksService(user=user),
            'gating': GatingService(),
            'grade_utils': GradesUtilService(course_id=course_id),
            'user_state': UserStateService(),
            'content_type_gating': ContentTypeGatingService(),
        },
        get_user_role=lambda: get_user_role(user, course_id),
        descriptor_runtime=descriptor._runtime,  # pylint: disable=protected-access
        rebind_noauth_module_to_user=rebind_noauth_module_to_user,
        user_location=user_location,
        request_token=request_token,
    )

    # pass position specified in URL to module through ModuleSystem
    if position is not None:
        try:
            position = int(position)
        except (ValueError, TypeError):
            log.exception(u'Non-integer %r passed as position.', position)
            position = None

    system.set('position', position)

    system.set(u'user_is_staff', user_is_staff)
    system.set(u'user_is_admin', bool(has_access(user, u'staff', 'global')))
    system.set(u'user_is_beta_tester', CourseBetaTesterRole(course_id).has_user(user))
    system.set(u'days_early_for_beta', descriptor.days_early_for_beta)

    # make an ErrorDescriptor -- assuming that the descriptor's system is ok
    if has_access(user, u'staff', descriptor.location, course_id):
        system.error_descriptor_class = ErrorDescriptor
    else:
        system.error_descriptor_class = NonStaffErrorDescriptor

    return system, field_data


# TODO: Find all the places that this method is called and figure out how to
# get a loaded course passed into it
def get_module_for_descriptor_internal(user, descriptor, student_data, course_id,
                                       track_function, xqueue_callback_url_prefix, request_token,
                                       position=None, wrap_xmodule_display=True, grade_bucket_type=None,
                                       static_asset_path='', user_location=None, disable_staff_debug_info=False,
                                       course=None, will_recheck_access=False):
    """
    Actually implement get_module, without requiring a request.

    See get_module() docstring for further details.

    Arguments:
        request_token (str): A unique token for this request, used to isolate xblock rendering
    """

    (system, student_data) = get_module_system_for_user(
        user=user,
        student_data=student_data,  # These have implicit user bindings, the rest of args are considered not to
        descriptor=descriptor,
        course_id=course_id,
        track_function=track_function,
        xqueue_callback_url_prefix=xqueue_callback_url_prefix,
        position=position,
        wrap_xmodule_display=wrap_xmodule_display,
        grade_bucket_type=grade_bucket_type,
        static_asset_path=static_asset_path,
        user_location=user_location,
        request_token=request_token,
        disable_staff_debug_info=disable_staff_debug_info,
        course=course,
        will_recheck_access=will_recheck_access,
    )

    descriptor.bind_for_student(
        system,
        user.id,
        [
            partial(DateLookupFieldData, course_id=course_id, user=user),
            partial(OverrideFieldData.wrap, user, course),
            partial(LmsFieldData, student_data=student_data),
        ],
    )

    descriptor.scope_ids = descriptor.scope_ids._replace(user_id=user.id)

    # Do not check access when it's a noauth request.
    # Not that the access check needs to happen after the descriptor is bound
    # for the student, since there may be field override data for the student
    # that affects xblock visibility.
    user_needs_access_check = getattr(user, 'known', True) and not isinstance(user, SystemUser)
    if user_needs_access_check:
        access = has_access(user, 'load', descriptor, course_id)
        # A descriptor should only be returned if either the user has access, or the user doesn't have access, but
        # the failed access has a message for the user and the caller of this function specifies it will check access
        # again. This allows blocks to show specific error message or upsells when access is denied.
        caller_will_handle_access_error = (
            not access
            and will_recheck_access
            and (access.user_message or access.user_fragment)
        )
        if access or caller_will_handle_access_error:
            return descriptor
        return None
    return descriptor


def load_single_xblock(request, user_id, course_id, usage_key_string, course=None, will_recheck_access=False):
    """
    Load a single XBlock identified by usage_key_string.
    """
    usage_key = UsageKey.from_string(usage_key_string)
    course_key = CourseKey.from_string(course_id)
    usage_key = usage_key.map_into_course(course_key)
    user = User.objects.get(id=user_id)
    field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
        course_key,
        user,
        modulestore().get_item(usage_key),
        depth=0,
    )
    instance = get_module(
        user,
        request,
        usage_key,
        field_data_cache,
        grade_bucket_type='xqueue',
        course=course,
        will_recheck_access=will_recheck_access
    )
    if instance is None:
        msg = u"No module {0} for user {1}--access denied?".format(usage_key_string, user)
        log.debug(msg)
        raise Http404
    return instance


@csrf_exempt
def xqueue_callback(request, course_id, userid, mod_id, dispatch):
    '''
    Entry point for graded results from the queueing system.
    '''
    data = request.POST.copy()

    # Test xqueue package, which we expect to be:
    #   xpackage = {'xqueue_header': json.dumps({'lms_key':'secretkey',...}),
    #               'xqueue_body'  : 'Message from grader'}
    for key in ['xqueue_header', 'xqueue_body']:
        if key not in data:
            raise Http404

    header = json.loads(data['xqueue_header'])
    if not isinstance(header, dict) or 'lms_key' not in header:
        raise Http404

    course_key = CourseKey.from_string(course_id)

    with modulestore().bulk_operations(course_key):
        course = modulestore().get_course(course_key, depth=0)

        instance = load_single_xblock(request, userid, course_id, mod_id, course=course)

        # Transfer 'queuekey' from xqueue response header to the data.
        # This is required to use the interface defined by 'handle_ajax'
        data.update({'queuekey': header['lms_key']})

        # We go through the "AJAX" path
        # So far, the only dispatch from xqueue will be 'score_update'
        try:
            # Can ignore the return value--not used for xqueue_callback
            instance.handle_ajax(dispatch, data)
            # Save any state that has changed to the underlying KeyValueStore
            instance.save()
        except:
            log.exception("error processing ajax call")
            raise

        return HttpResponse("")


@csrf_exempt
@xframe_options_exempt
@transaction.non_atomic_requests
def handle_xblock_callback_noauth(request, course_id, usage_id, handler, suffix=None):
    """
    Entry point for unauthenticated XBlock handlers.
    """
    request.user.known = False

    course_key = CourseKey.from_string(course_id)
    with modulestore().bulk_operations(course_key):
        course = modulestore().get_course(course_key, depth=0)
        return _invoke_xblock_handler(request, course_id, usage_id, handler, suffix, course=course)


@csrf_exempt
@xframe_options_exempt
@transaction.non_atomic_requests
def handle_xblock_callback(request, course_id, usage_id, handler, suffix=None):
    """
    Generic view for extensions. This is where AJAX calls go.

    Arguments:
        request (Request): Django request.
        course_id (str): Course containing the block
        usage_id (str)
        handler (str)
        suffix (str)

    Raises:
        HttpResponseForbidden: If the request method is not `GET` and user is not authenticated.
        Http404: If the course is not found in the modulestore.
    """
    # In this case, we are using Session based authentication, so we need to check CSRF token.
    if request.user.is_authenticated:
        error = CsrfViewMiddleware().process_view(request, None, (), {})
        if error:
            return error

    # We are reusing DRF logic to provide support for JWT and Oauth2. We abandoned the idea of using DRF view here
    # to avoid introducing backwards-incompatible changes.
    # You can see https://github.com/edx/XBlock/pull/383 for more details.
    else:
        authentication_classes = (JwtAuthentication, BearerAuthenticationAllowInactiveUser)
        authenticators = [auth() for auth in authentication_classes]

        for authenticator in authenticators:
            try:
                user_auth_tuple = authenticator.authenticate(request)
            except APIException:
                log.exception(
                    u"XBlock handler %r failed to authenticate with %s", handler, authenticator.__class__.__name__
                )
            else:
                if user_auth_tuple is not None:
                    request.user, _ = user_auth_tuple
                    break

    # NOTE (CCB): Allow anonymous GET calls (e.g. for transcripts). Modifying this view is simpler than updating
    # the XBlocks to use `handle_xblock_callback_noauth`, which is practically identical to this view.
    if request.method != 'GET' and not (request.user and request.user.is_authenticated):
        return HttpResponseForbidden('Unauthenticated')

    request.user.known = request.user.is_authenticated

    try:
        course_key = CourseKey.from_string(course_id)
    except InvalidKeyError:
        raise Http404(u'{} is not a valid course key'.format(course_id))

    with modulestore().bulk_operations(course_key):
        try:
            course = modulestore().get_course(course_key)
        except ItemNotFoundError:
            raise Http404(u'{} does not exist in the modulestore'.format(course_id))

        return _invoke_xblock_handler(request, course_id, usage_id, handler, suffix, course=course)


def get_module_by_usage_id(request, course_id, usage_id, disable_staff_debug_info=False, course=None):
    """
    Gets a module instance based on its `usage_id` in a course, for a given request/user

    Returns (instance, tracking_context)
    """
    user = request.user

    try:
        course_id = CourseKey.from_string(course_id)
        usage_key = UsageKey.from_string(unquote_slashes(usage_id)).map_into_course(course_id)
    except InvalidKeyError:
        raise Http404("Invalid location")

    try:
        descriptor = modulestore().get_item(usage_key)
        descriptor_orig_usage_key, descriptor_orig_version = modulestore().get_block_original_usage(usage_key)
    except ItemNotFoundError:
        log.warning(
            u"Invalid location for course id %s: %s",
            usage_key.course_key,
            usage_key
        )
        raise Http404

    tracking_context = {
        'module': {
            # xss-lint: disable=python-deprecated-display-name
            'display_name': descriptor.display_name_with_default_escaped,
            'usage_key': six.text_type(descriptor.location),
        }
    }

    # For blocks that are inherited from a content library, we add some additional metadata:
    if descriptor_orig_usage_key is not None:
        tracking_context['module']['original_usage_key'] = six.text_type(descriptor_orig_usage_key)
        tracking_context['module']['original_usage_version'] = six.text_type(descriptor_orig_version)

    unused_masquerade, user = setup_masquerade(request, course_id, has_access(user, 'staff', descriptor, course_id))
    field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
        course_id,
        user,
        descriptor,
        read_only=CrawlersConfig.is_crawler(request),
    )
    instance = get_module_for_descriptor(
        user,
        request,
        descriptor,
        field_data_cache,
        usage_key.course_key,
        disable_staff_debug_info=disable_staff_debug_info,
        course=course
    )
    if instance is None:
        # Either permissions just changed, or someone is trying to be clever
        # and load something they shouldn't have access to.
        log.debug(u"No module %s for user %s -- access denied?", usage_key, user)
        raise Http404

    return (instance, tracking_context)


def _invoke_xblock_handler(request, course_id, usage_id, handler, suffix, course=None):
    """
    Invoke an XBlock handler, either authenticated or not.

    Arguments:
        request (HttpRequest): the current request
        course_id (str): A string of the form org/course/run
        usage_id (str): A string of the form i4x://org/course/category/name@revision
        handler (str): The name of the handler to invoke
        suffix (str): The suffix to pass to the handler when invoked
    """

    # Check submitted files
    files = request.FILES or {}
    error_msg = _check_files_limits(files)
    if error_msg:
        return JsonResponse({'success': error_msg}, status=413)

    # Make a CourseKey from the course_id, raising a 404 upon parse error.
    try:
        course_key = CourseKey.from_string(course_id)
    except InvalidKeyError:
        raise Http404

    set_custom_attributes_for_course_key(course_key)

    with modulestore().bulk_operations(course_key):
        try:
            usage_key = UsageKey.from_string(unquote_slashes(usage_id))
        except InvalidKeyError:
            raise Http404
        if is_xblock_aside(usage_key):
            # Get the usage key for the block being wrapped by the aside (not the aside itself)
            block_usage_key = usage_key.usage_key
        else:
            block_usage_key = usage_key
        instance, tracking_context = get_module_by_usage_id(
            request, course_id, six.text_type(block_usage_key), course=course
        )

        # Name the transaction so that we can view XBlock handlers separately in
        # New Relic. The suffix is necessary for XModule handlers because the
        # "handler" in those cases is always just "xmodule_handler".
        nr_tx_name = "{}.{}".format(instance.__class__.__name__, handler)
        nr_tx_name += "/{}".format(suffix) if (suffix and handler == "xmodule_handler") else ""
        set_monitoring_transaction_name(nr_tx_name, group="Python/XBlock/Handler")

        tracking_context_name = 'module_callback_handler'
        req = django_to_webob_request(request)
        try:
            with tracker.get_tracker().context(tracking_context_name, tracking_context):
                if is_xblock_aside(usage_key):
                    # In this case, 'instance' is the XBlock being wrapped by the aside, so
                    # the actual aside instance needs to be retrieved in order to invoke its
                    # handler method.
                    handler_instance = get_aside_from_xblock(instance, usage_key.aside_type)
                else:
                    handler_instance = instance
                resp = handler_instance.handle(handler, req, suffix)
                if suffix == 'problem_check' \
                        and course \
                        and getattr(course, 'entrance_exam_enabled', False) \
                        and getattr(instance, 'in_entrance_exam', False):
                    ee_data = {'entrance_exam_passed': user_has_passed_entrance_exam(request.user, course)}
                    resp = append_data_to_webob_response(resp, ee_data)

        except NoSuchHandlerError:
            log.exception(u"XBlock %s attempted to access missing handler %r", instance, handler)
            raise Http404

        # If we can't find the module, respond with a 404
        except NotFoundError:
            log.exception("Module indicating to user that request doesn't exist")
            raise Http404

        # For XModule-specific errors, we log the error and respond with an error message
        except ProcessingError as err:
            log.warning("Module encountered an error while processing AJAX call",
                        exc_info=True)
            return JsonResponse({'success': err.args[0]}, status=200)

        # If any other error occurred, re-raise it to trigger a 500 response
        except Exception:
            log.exception("error executing xblock handler")
            raise

    return webob_to_django_response(resp)


@api_view(['GET'])
@view_auth_classes(is_authenticated=True)
def xblock_view(request, course_id, usage_id, view_name):
    """
    Returns the rendered view of a given XBlock, with related resources

    Returns a json object containing two keys:
        html: The rendered html of the view
        resources: A list of tuples where the first element is the resource hash, and
            the second is the resource description
    """
    if not settings.FEATURES.get('ENABLE_XBLOCK_VIEW_ENDPOINT', False):
        log.warning("Attempt to use deactivated XBlock view endpoint -"
                    " see FEATURES['ENABLE_XBLOCK_VIEW_ENDPOINT']")
        raise Http404

    try:
        course_key = CourseKey.from_string(course_id)
    except InvalidKeyError:
        raise Http404("Invalid location")

    with modulestore().bulk_operations(course_key):
        course = modulestore().get_course(course_key)
        instance, _ = get_module_by_usage_id(request, course_id, usage_id, course=course)

        try:
            fragment = instance.render(view_name, context=request.GET)
        except NoSuchViewError:
            log.exception(u"Attempt to render missing view on %s: %s", instance, view_name)
            raise Http404

        hashed_resources = OrderedDict()
        for resource in fragment.resources:
            hashed_resources[hash_resource(resource)] = resource

        return JsonResponse({
            'html': fragment.content,
            'resources': list(hashed_resources.items()),
            'csrf_token': six.text_type(csrf(request)['csrf_token']),
        })


def _check_files_limits(files):
    """
    Check if the files in a request are under the limits defined by
    `settings.MAX_FILEUPLOADS_PER_INPUT` and
    `settings.STUDENT_FILEUPLOAD_MAX_SIZE`.

    Returns None if files are correct or an error messages otherwise.
    """
    for fileinput_id in files.keys():
        inputfiles = files.getlist(fileinput_id)

        # Check number of files submitted
        if len(inputfiles) > settings.MAX_FILEUPLOADS_PER_INPUT:
            msg = u'Submission aborted! Maximum %d files may be submitted at once' % \
                  settings.MAX_FILEUPLOADS_PER_INPUT
            return msg

        # Check file sizes
        for inputfile in inputfiles:
            if inputfile.size > settings.STUDENT_FILEUPLOAD_MAX_SIZE:  # Bytes
                msg = u'Submission aborted! Your file "%s" is too large (max size: %d MB)' % \
                      (inputfile.name, settings.STUDENT_FILEUPLOAD_MAX_SIZE / (1000 ** 2))
                return msg

    return None


def append_data_to_webob_response(response, data):
    """
    Appends data to a JSON webob response.

    Arguments:
        response (webob response object):  the webob response object that needs to be modified
        data (dict):  dictionary containing data that needs to be appended to response body

    Returns:
        (webob response object):  webob response with updated body.

    """
    if getattr(response, 'content_type', None) == 'application/json':
        json_input = response.body.decode('utf-8') if isinstance(response.body, bytes) else response.body
        response_data = json.loads(json_input)
        response_data.update(data)
        response.body = json.dumps(response_data).encode('utf-8')
    return response
