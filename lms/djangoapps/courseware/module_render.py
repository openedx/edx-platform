"""
Module rendering
"""

import hashlib
import json
import logging

import static_replace

from collections import OrderedDict
from functools import partial
from requests.auth import HTTPBasicAuth
import dogstats_wrapper as dog_stats_api

from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.context_processors import csrf
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponse
from django.test.client import RequestFactory
from django.views.decorators.csrf import csrf_exempt

import newrelic.agent

from capa.xqueue_interface import XQueueInterface
from courseware.access import has_access, get_user_role
from courseware.masquerade import (
    MasqueradingKeyValueStore,
    filter_displayed_blocks,
    is_masquerading_as_specific_student,
    setup_masquerade,
)
from courseware.model_data import DjangoKeyValueStore, FieldDataCache, set_score
from courseware.models import SCORE_CHANGED
from courseware.entrance_exams import (
    get_entrance_exam_score,
    user_must_complete_entrance_exam,
    user_has_passed_entrance_exam
)
from edxmako.shortcuts import render_to_string
from eventtracking import tracker
from lms.djangoapps.lms_xblock.field_data import LmsFieldData
from lms.djangoapps.lms_xblock.runtime import LmsModuleSystem, unquote_slashes, quote_slashes
from lms.djangoapps.lms_xblock.models import XBlockAsidesConfig
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import UsageKey, CourseKey
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from openedx.core.lib.inline_analytics_utils import add_inline_analytics
from openedx.core.lib.xblock_utils import (
    replace_course_urls,
    replace_jump_to_id_urls,
    replace_static_urls,
    add_staff_markup,
    wrap_xblock,
    request_token as xblock_request_token,
)
from psychometrics.psychoanalyze import make_psychometrics_data_update_handler
from student.models import anonymous_id_for_user, user_by_anonymous_id
from student.roles import CourseBetaTesterRole
from xblock.core import XBlock
from xblock.django.request import django_to_webob_request, webob_to_django_response
from xblock_django.user_service import DjangoXBlockUserService
from xblock.exceptions import NoSuchHandlerError, NoSuchViewError
from xblock.reference.plugins import FSService
from xblock.runtime import KvsFieldData
from xmodule.contentstore.django import contentstore
from xmodule.error_module import ErrorDescriptor, NonStaffErrorDescriptor
from xmodule.exceptions import NotFoundError, ProcessingError
from xmodule.modulestore.django import modulestore, ModuleI18nService
from xmodule.lti_module import LTIModule
from xmodule.modulestore.exceptions import ItemNotFoundError
from xmodule.x_module import XModuleDescriptor
from xmodule.mixin import wrap_with_license
from util.json_request import JsonResponse
from util.keyword_substitution import substitute_keywords_with_data
from util.model_utils import slugify
from util.sandboxing import can_execute_unsafe_code, get_python_lib_zip
from util import milestones_helpers
from lms.djangoapps.verify_student.services import ReverificationService

from edx_proctoring.services import ProctoringService
from openedx.core.djangoapps.credit.services import CreditService

from .field_overrides import OverrideFieldData

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
    import track.views

    def function(event_type, event):
        return track.views.server_track(request, event_type, event, page='x_module')
    return function


def toc_for_course(user, request, course, active_chapter, active_section, field_data_cache):
    '''
    Create a table of contents from the module store

    Return format:
    [ {'display_name': name, 'url_name': url_name,
       'sections': SECTIONS, 'active': bool}, ... ]

    where SECTIONS is a list
    [ {'display_name': name, 'url_name': url_name,
       'format': format, 'due': due, 'active' : bool, 'graded': bool}, ...]

    active is set for the section and chapter corresponding to the passed
    parameters, which are expected to be url_names of the chapter+section.
    Everything else comes from the xml, or defaults to "".

    chapters with name 'hidden' are skipped.

    NOTE: assumes that if we got this far, user has access to course.  Returns
    None if this is not the case.

    field_data_cache must include data from the course module and 2 levels of its descendents
    '''

    with modulestore().bulk_operations(course.id):
        course_module = get_module_for_descriptor(
            user, request, course, field_data_cache, course.id, course=course
        )
        if course_module is None:
            return None

        toc_chapters = list()
        chapters = course_module.get_display_items()

        # See if the course is gated by one or more content milestones
        required_content = milestones_helpers.get_required_content(course, user)

        # The user may not actually have to complete the entrance exam, if one is required
        if not user_must_complete_entrance_exam(request, user, course):
            required_content = [content for content in required_content if not content == course.entrance_exam_id]

        for chapter in chapters:
            # Only show required content, if there is required content
            # chapter.hide_from_toc is read-only (boo)
            display_id = slugify(chapter.display_name_with_default)
            local_hide_from_toc = False
            if required_content:
                if unicode(chapter.location) not in required_content:
                    local_hide_from_toc = True

            # Skip the current chapter if a hide flag is tripped
            if chapter.hide_from_toc or local_hide_from_toc:
                continue

            sections = list()
            for section in chapter.get_display_items():

                active = (chapter.url_name == active_chapter and
                          section.url_name == active_section)

                if not section.hide_from_toc:
                    section_context = {
                        'display_name': section.display_name_with_default,
                        'url_name': section.url_name,
                        'format': section.format if section.format is not None else '',
                        'due': section.due,
                        'active': active,
                        'graded': section.graded,
                    }

                    #
                    # Add in rendering context if exam is a timed exam (which includes proctored)
                    #

                    section_is_time_limited = (
                        getattr(section, 'is_time_limited', False) and
                        settings.FEATURES.get('ENABLE_SPECIAL_EXAMS', False)
                    )
                    if section_is_time_limited:
                        # We need to import this here otherwise Lettuce test
                        # harness fails. When running in 'harvest' mode, the
                        # test service appears to get into trouble with
                        # circular references (not sure which as edx_proctoring.api
                        # doesn't import anything from edx-platform). Odd thing
                        # is that running: manage.py lms runserver --settings=acceptance
                        # works just fine, it's really a combination of Lettuce and the
                        # 'harvest' management command
                        #
                        # One idea is that there is some coupling between
                        # lettuce and the 'terrain' Djangoapps projects in /common
                        # This would need more investigation
                        from edx_proctoring.api import get_attempt_status_summary

                        #
                        # call into edx_proctoring subsystem
                        # to get relevant proctoring information regarding this
                        # level of the courseware
                        #
                        # This will return None, if (user, course_id, content_id)
                        # is not applicable
                        #
                        timed_exam_attempt_context = None
                        try:
                            timed_exam_attempt_context = get_attempt_status_summary(
                                user.id,
                                unicode(course.id),
                                unicode(section.location)
                            )
                        except Exception, ex:  # pylint: disable=broad-except
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

                    sections.append(section_context)
            toc_chapters.append({
                'display_name': chapter.display_name_with_default,
                'display_id': display_id,
                'url_name': chapter.url_name,
                'sections': sections,
                'active': chapter.url_name == active_chapter
            })
        return toc_chapters


def get_module(user, request, usage_key, field_data_cache,
               position=None, log_if_not_found=True, wrap_xmodule_display=True,
               grade_bucket_type=None, depth=0,
               static_asset_path='', course=None):
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
                                         course=course)
    except ItemNotFoundError:
        if log_if_not_found:
            log.debug("Error in get_module: ItemNotFoundError")
        return None

    except:
        # Something has gone terribly wrong, but still not letting it turn into a 500.
        log.exception("Error in get_module")
        return None


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


def get_module_for_descriptor(user, request, descriptor, field_data_cache, course_key,
                              position=None, wrap_xmodule_display=True, grade_bucket_type=None,
                              static_asset_path='', disable_staff_debug_info=False,
                              course=None):
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
        course=course
    )


def get_module_system_for_user(user, student_data,  # TODO  # pylint: disable=too-many-statements
                               # Arguments preceding this comment have user binding, those following don't
                               descriptor, course_id, track_function, xqueue_callback_url_prefix,
                               request_token, position=None, wrap_xmodule_display=True, grade_bucket_type=None,
                               static_asset_path='', user_location=None, disable_staff_debug_info=False,
                               course=None):
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
                course_id=course_id.to_deprecated_string(),
                userid=str(user.id),
                mod_id=descriptor.location.to_deprecated_string(),
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

    # This is a hacky way to pass settings to the combined open ended xmodule
    # It needs an S3 interface to upload images to S3
    # It needs the open ended grading interface in order to get peer grading to be done
    # this first checks to see if the descriptor is the correct one, and only sends settings if it is

    # Get descriptor metadata fields indicating needs for various settings
    needs_open_ended_interface = getattr(descriptor, "needs_open_ended_interface", False)
    needs_s3_interface = getattr(descriptor, "needs_s3_interface", False)

    # Initialize interfaces to None
    open_ended_grading_interface = None
    s3_interface = None

    # Create interfaces if needed
    if needs_open_ended_interface:
        open_ended_grading_interface = settings.OPEN_ENDED_GRADING_INTERFACE
        open_ended_grading_interface['mock_peer_grading'] = settings.MOCK_PEER_GRADING
        open_ended_grading_interface['mock_staff_grading'] = settings.MOCK_STAFF_GRADING
    if needs_s3_interface:
        s3_interface = {
            'access_key': getattr(settings, 'AWS_ACCESS_KEY_ID', ''),
            'secret_access_key': getattr(settings, 'AWS_SECRET_ACCESS_KEY', ''),
            'storage_bucket_name': getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'openended')
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
            course=course
        )

    def _fulfill_content_milestones(user, course_key, content_key):
        """
        Internal helper to handle milestone fulfillments for the specified content module
        """
        # Fulfillment Use Case: Entrance Exam
        # If this module is part of an entrance exam, we'll need to see if the student
        # has reached the point at which they can collect the associated milestone
        if milestones_helpers.is_entrance_exams_enabled():
            course = modulestore().get_course(course_key)
            content = modulestore().get_item(content_key)
            entrance_exam_enabled = getattr(course, 'entrance_exam_enabled', False)
            in_entrance_exam = getattr(content, 'in_entrance_exam', False)
            if entrance_exam_enabled and in_entrance_exam:
                # We don't have access to the true request object in this context, but we can use a mock
                request = RequestFactory().request()
                request.user = user
                exam_pct = get_entrance_exam_score(request, course)
                if exam_pct >= course.entrance_exam_minimum_score_pct:
                    exam_key = UsageKey.from_string(course.entrance_exam_id)
                    relationship_types = milestones_helpers.get_milestone_relationship_types()
                    content_milestones = milestones_helpers.get_course_content_milestones(
                        course_key,
                        exam_key,
                        relationship=relationship_types['FULFILLS']
                    )
                    # Add each milestone to the user's set...
                    user = {'id': request.user.id}
                    for milestone in content_milestones:
                        milestones_helpers.add_user_milestone(user, milestone)

    def handle_grade_event(block, event_type, event):  # pylint: disable=unused-argument
        """
        Manages the workflow for recording and updating of student module grade state
        """
        user_id = event.get('user_id', user.id)

        grade = event.get('value')
        max_grade = event.get('max_value')

        set_score(
            user_id,
            descriptor.location,
            grade,
            max_grade,
        )

        # Bin score into range and increment stats
        score_bucket = get_score_bucket(grade, max_grade)

        tags = [
            u"org:{}".format(course_id.org),
            u"course:{}".format(course_id),
            u"score_bucket:{0}".format(score_bucket)
        ]

        if grade_bucket_type is not None:
            tags.append('type:%s' % grade_bucket_type)

        dog_stats_api.increment("lms.courseware.question_answered", tags=tags)

        # Cycle through the milestone fulfillment scenarios to see if any are now applicable
        # thanks to the updated grading information that was just submitted
        _fulfill_content_milestones(
            user,
            course_id,
            descriptor.location,
        )

        # Send a signal out to any listeners who are waiting for score change
        # events.
        SCORE_CHANGED.send(
            sender=None,
            points_possible=event['max_value'],
            points_earned=event['value'],
            user_id=user_id,
            course_id=unicode(course_id),
            usage_id=unicode(descriptor.location)
        )

    def publish(block, event_type, event):
        """A function that allows XModules to publish events."""
        if event_type == 'grade' and not is_masquerading_as_specific_student(user, course_id):
            handle_grade_event(block, event_type, event)
        else:
            track_function(event_type, event)

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
        if user.is_authenticated():
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
            course=course
        )

        module.descriptor.bind_for_student(
            inner_system,
            real_user.id,
            [
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
            extra_data={'course-id': course_id.to_deprecated_string()},
            usage_id_serializer=lambda usage_id: quote_slashes(usage_id.to_deprecated_string()),
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
        reverse('jump_to_id', kwargs={'course_id': course_id.to_deprecated_string(), 'module_id': ''}),
    ))

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
            instructor_access = bool(has_access(user.real_user, 'instructor', descriptor, course_id))
            user.real_user.masquerade_settings = masquerade_settings
        else:
            staff_access = has_access(user, 'staff', descriptor, course_id)
            instructor_access = bool(has_access(user, 'instructor', descriptor, course_id))
        if staff_access:
            block_wrappers.append(partial(add_staff_markup, user, instructor_access, disable_staff_debug_info))

    # Add button for in-line analytics answer distribution
    if getattr(settings, 'ANALYTICS_DATA_URL'):
        if has_access(user, 'staff', descriptor, course_id):
            block_wrappers.append(partial(add_inline_analytics, user))

    # These modules store data using the anonymous_student_id as a key.
    # To prevent loss of data, we will continue to provide old modules with
    # the per-student anonymized id (as we have in the past),
    # while giving selected modules a per-course anonymized id.
    # As we have the time to manually test more modules, we can add to the list
    # of modules that get the per-course anonymized id.
    is_pure_xblock = isinstance(descriptor, XBlock) and not isinstance(descriptor, XModuleDescriptor)
    module_class = getattr(descriptor, 'module_class', None)
    is_lti_module = not is_pure_xblock and issubclass(module_class, LTIModule)
    if is_pure_xblock or is_lti_module:
        anonymous_student_id = anonymous_id_for_user(user, course_id)
    else:
        anonymous_student_id = anonymous_id_for_user(user, None)

    field_data = LmsFieldData(descriptor._field_data, student_data)  # pylint: disable=protected-access

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
            jump_to_id_base_url=reverse('jump_to_id', kwargs={'course_id': course_id.to_deprecated_string(), 'module_id': ''})
        ),
        node_path=settings.NODE_PATH,
        publish=publish,
        anonymous_student_id=anonymous_student_id,
        course_id=course_id,
        open_ended_grading_interface=open_ended_grading_interface,
        s3_interface=s3_interface,
        cache=cache,
        can_execute_unsafe_code=(lambda: can_execute_unsafe_code(course_id)),
        get_python_lib_zip=(lambda: get_python_lib_zip(contentstore, course_id)),
        # TODO: When we merge the descriptor and module systems, we can stop reaching into the mixologist (cpennington)
        mixins=descriptor.runtime.mixologist._mixins,  # pylint: disable=protected-access
        wrappers=block_wrappers,
        get_real_user=user_by_anonymous_id,
        services={
            'i18n': ModuleI18nService(),
            'fs': FSService(),
            'field-data': field_data,
            'user': DjangoXBlockUserService(user, user_is_staff=user_is_staff),
            "reverification": ReverificationService(),
            'proctoring': ProctoringService(),
            'credit': CreditService(),
        },
        get_user_role=lambda: get_user_role(user, course_id),
        descriptor_runtime=descriptor._runtime,  # pylint: disable=protected-access
        rebind_noauth_module_to_user=rebind_noauth_module_to_user,
        user_location=user_location,
        substitute_keywords_with_data=partial(substitute_keywords_with_data),
        request_token=request_token,
    )
    if settings.FEATURES.get('SEND_USERS_EMAILADDR_WITH_CODERESPONSE', False):
        system.set('send_users_emailaddr_with_coderesponse', True)
        if user.is_authenticated():
            system.set('deanonymized_user_email', user.email)
        else:
            system.set('deanonymized_user_email', '')

    # pass position specified in URL to module through ModuleSystem
    if position is not None:
        try:
            position = int(position)
        except (ValueError, TypeError):
            log.exception('Non-integer %r passed as position.', position)
            position = None

    system.set('position', position)
    if settings.FEATURES.get('ENABLE_PSYCHOMETRICS') and user.is_authenticated():
        system.set(
            'psychometrics_handler',  # set callback for updating PsychometricsData
            make_psychometrics_data_update_handler(course_id, user, descriptor.location)
        )

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
def get_module_for_descriptor_internal(user, descriptor, student_data, course_id,  # pylint: disable=invalid-name
                                       track_function, xqueue_callback_url_prefix, request_token,
                                       position=None, wrap_xmodule_display=True, grade_bucket_type=None,
                                       static_asset_path='', user_location=None, disable_staff_debug_info=False,
                                       course=None):
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
        course=course
    )

    descriptor.bind_for_student(
        system,
        user.id,
        [
            partial(OverrideFieldData.wrap, user, course),
            partial(LmsFieldData, student_data=student_data),
        ],
    )

    descriptor.scope_ids = descriptor.scope_ids._replace(user_id=user.id)

    # Do not check access when it's a noauth request.
    # Not that the access check needs to happen after the descriptor is bound
    # for the student, since there may be field override data for the student
    # that affects xblock visibility.
    if getattr(user, 'known', True):
        if not has_access(user, 'load', descriptor, course_id):
            return None

    return descriptor


def load_single_xblock(request, user_id, course_id, usage_key_string, course=None):
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
    instance = get_module(user, request, usage_key, field_data_cache, grade_bucket_type='xqueue', course=course)
    if instance is None:
        msg = "No module {0} for user {1}--access denied?".format(usage_key_string, user)
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
def handle_xblock_callback_noauth(request, course_id, usage_id, handler, suffix=None):
    """
    Entry point for unauthenticated XBlock handlers.
    """
    request.user.known = False

    course_key = CourseKey.from_string(course_id)
    with modulestore().bulk_operations(course_key):
        course = modulestore().get_course(course_key, depth=0)
        return _invoke_xblock_handler(request, course_id, usage_id, handler, suffix, course=course)


def handle_xblock_callback(request, course_id, usage_id, handler, suffix=None):
    """
    Generic view for extensions. This is where AJAX calls go.

    Arguments:

      - request -- the django request.
      - location -- the module location. Used to look up the XModule instance
      - course_id -- defines the course context for this request.

    Return 403 error if the user is not logged in. Raises Http404 if
    the location and course_id do not identify a valid module, the module is
    not accessible by the user, or the module raises NotFoundError. If the
    module raises any other error, it will escape this function.
    """
    if not request.user.is_authenticated():
        return HttpResponse('Unauthenticated', status=403)

    try:
        course_key = CourseKey.from_string(course_id)
    except InvalidKeyError:
        raise Http404("Invalid location")

    with modulestore().bulk_operations(course_key):
        try:
            course = modulestore().get_course(course_key)
        except ItemNotFoundError:
            raise Http404("invalid location")

        return _invoke_xblock_handler(request, course_id, usage_id, handler, suffix, course=course)


def get_module_by_usage_id(request, course_id, usage_id, disable_staff_debug_info=False, course=None):
    """
    Gets a module instance based on its `usage_id` in a course, for a given request/user

    Returns (instance, tracking_context)
    """
    user = request.user

    try:
        course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)
        usage_key = course_id.make_usage_key_from_deprecated_string(unquote_slashes(usage_id))
    except InvalidKeyError:
        raise Http404("Invalid location")

    try:
        descriptor = modulestore().get_item(usage_key)
        descriptor_orig_usage_key, descriptor_orig_version = modulestore().get_block_original_usage(usage_key)
    except ItemNotFoundError:
        log.warn(
            "Invalid location for course id %s: %s",
            usage_key.course_key,
            usage_key
        )
        raise Http404

    tracking_context = {
        'module': {
            'display_name': descriptor.display_name_with_default,
            'usage_key': unicode(descriptor.location),
        }
    }

    # For blocks that are inherited from a content library, we add some additional metadata:
    if descriptor_orig_usage_key is not None:
        tracking_context['module']['original_usage_key'] = unicode(descriptor_orig_usage_key)
        tracking_context['module']['original_usage_version'] = unicode(descriptor_orig_version)

    unused_masquerade, user = setup_masquerade(request, course_id, has_access(user, 'staff', descriptor, course_id))
    field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
        course_id,
        user,
        descriptor
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
        log.debug("No module %s for user %s -- access denied?", usage_key, user)
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

    with modulestore().bulk_operations(course_key):
        instance, tracking_context = get_module_by_usage_id(request, course_id, usage_id, course=course)

        # Name the transaction so that we can view XBlock handlers separately in
        # New Relic. The suffix is necessary for XModule handlers because the
        # "handler" in those cases is always just "xmodule_handler".
        nr_tx_name = "{}.{}".format(instance.__class__.__name__, handler)
        nr_tx_name += "/{}".format(suffix) if (suffix and handler == "xmodule_handler") else ""
        newrelic.agent.set_transaction_name(nr_tx_name, group="Python/XBlock/Handler")

        tracking_context_name = 'module_callback_handler'
        req = django_to_webob_request(request)
        try:
            with tracker.get_tracker().context(tracking_context_name, tracking_context):
                resp = instance.handle(handler, req, suffix)
                if suffix == 'problem_check' \
                        and course \
                        and getattr(course, 'entrance_exam_enabled', False) \
                        and getattr(instance, 'in_entrance_exam', False):
                    ee_data = {'entrance_exam_passed': user_has_passed_entrance_exam(request, course)}
                    resp = append_data_to_webob_response(resp, ee_data)

        except NoSuchHandlerError:
            log.exception("XBlock %s attempted to access missing handler %r", instance, handler)
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


def hash_resource(resource):
    """
    Hash a :class:`xblock.fragment.FragmentResource
    """
    md5 = hashlib.md5()
    for data in resource:
        md5.update(repr(data))
    return md5.hexdigest()


def xblock_view(request, course_id, usage_id, view_name):
    """
    Returns the rendered view of a given XBlock, with related resources

    Returns a json object containing two keys:
        html: The rendered html of the view
        resources: A list of tuples where the first element is the resource hash, and
            the second is the resource description
    """
    if not settings.FEATURES.get('ENABLE_XBLOCK_VIEW_ENDPOINT', False):
        log.warn("Attempt to use deactivated XBlock view endpoint -"
                 " see FEATURES['ENABLE_XBLOCK_VIEW_ENDPOINT']")
        raise Http404

    if not request.user.is_authenticated():
        raise PermissionDenied

    try:
        course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    except InvalidKeyError:
        raise Http404("Invalid location")

    with modulestore().bulk_operations(course_key):
        course = modulestore().get_course(course_key)
        instance, _ = get_module_by_usage_id(request, course_id, usage_id, course=course)

        try:
            fragment = instance.render(view_name, context=request.GET)
        except NoSuchViewError:
            log.exception("Attempt to render missing view on %s: %s", instance, view_name)
            raise Http404

        hashed_resources = OrderedDict()
        for resource in fragment.resources:
            hashed_resources[hash_resource(resource)] = resource

        return JsonResponse({
            'html': fragment.content,
            'resources': hashed_resources.items(),
            'csrf_token': unicode(csrf(request)['csrf_token']),
        })


def get_score_bucket(grade, max_grade):
    """
    Function to split arbitrary score ranges into 3 buckets.
    Used with statsd tracking.
    """
    score_bucket = "incorrect"
    if grade > 0 and grade < max_grade:
        score_bucket = "partial"
    elif grade == max_grade:
        score_bucket = "correct"

    return score_bucket


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
            msg = 'Submission aborted! Maximum %d files may be submitted at once' % \
                  settings.MAX_FILEUPLOADS_PER_INPUT
            return msg

        # Check file sizes
        for inputfile in inputfiles:
            if inputfile.size > settings.STUDENT_FILEUPLOAD_MAX_SIZE:  # Bytes
                msg = 'Submission aborted! Your file "%s" is too large (max size: %d MB)' % \
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
        response_data = json.loads(response.body)
        response_data.update(data)
        response.body = json.dumps(response_data)
    return response
