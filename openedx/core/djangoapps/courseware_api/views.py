"""
Course API Views
"""

import json

from babel.numbers import get_currency_symbol
from completion.exceptions import UnavailableCompletionData
from completion.utilities import get_key_to_last_completed_block
from django.conf import settings
from django.urls import reverse
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey, UsageKey
from rest_framework.exceptions import NotFound
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from course_modes.models import CourseMode
from edxnotes.helpers import is_feature_enabled
from lms.djangoapps.course_api.api import course_detail
from lms.djangoapps.courseware.access import has_access
from lms.djangoapps.courseware.access_response import (
    CoursewareMicrofrontendDisabledAccessError,
)
from lms.djangoapps.courseware.courses import check_course_access, get_course_by_id
from lms.djangoapps.courseware.masquerade import setup_masquerade
from lms.djangoapps.courseware.module_render import get_module_by_usage_id
from lms.djangoapps.courseware.tabs import get_course_tab_list
from lms.djangoapps.courseware.toggles import REDIRECT_TO_COURSEWARE_MICROFRONTEND
from lms.djangoapps.courseware.utils import can_show_verified_upgrade
from lms.djangoapps.courseware.utils import verified_upgrade_deadline_link
from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin
from openedx.features.course_experience import DISPLAY_COURSE_SOCK_FLAG
from openedx.features.content_type_gating.models import ContentTypeGatingConfig
from openedx.features.course_duration_limits.access import generate_course_expired_message
from openedx.features.discounts.utils import generate_offer_html
from student.models import CourseEnrollment, CourseEnrollmentCelebration
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.search import path_to_location

from .serializers import CourseInfoSerializer


class CoursewareMeta:
    """
    Encapsulates courseware and enrollment metadata.
    """
    def __init__(self, course_key, request, username=''):
        self.overview = course_detail(
            request,
            username or request.user.username,
            course_key,
        )
        self.effective_user = self.overview.effective_user
        self.original_user_is_staff = has_access(request.user, 'staff', self.overview).has_access
        self.course_key = course_key
        self.enrollment_object = CourseEnrollment.get_enrollment(self.effective_user, self.course_key,
                                                                 select_related=['celebration'])
        course_masquerade, user = setup_masquerade(
            request,
            course_key,
            staff_access=self.original_user_is_staff,
        )
        self.is_staff = has_access(user, 'staff', self.overview).has_access
        self.course_masquerade = course_masquerade

    def __getattr__(self, name):
        return getattr(self.overview, name)

    def is_microfrontend_enabled_for_user(self):
        """
        This method is the "opposite" of _redirect_to_learning_mfe in
        lms/djangoapps/courseware/views/index.py. But not exactly...

        1. It needs to respect the global
           ENABLE_COURSEWARE_MICROFRONTEND feature flag and redirect users
           out of the MFE experience if it's turned off.
        2. It needs to redirect for old Mongo courses.
        3. It does NOT need to worry about exams - the MFE will handle
           those on its own. As of this writing, it will redirect back to
           the LMS experience, but that may change soon.
        4. Finally, it needs to redirect users who are bucketed out of
           the MFE experience, but who aren't staff. Staff are allowed to
           stay.
        """
        # REDIRECT: feature disabled globally
        if not settings.FEATURES.get('ENABLE_COURSEWARE_MICROFRONTEND'):
            return False
        # REDIRECT: Old Mongo courses, until removed from platform
        if self.course_key.deprecated:
            return False
        # REDIRECT: If the user isn't staff, redirect if they're bucketed into the old LMS experience.
        if not self.original_user_is_staff and not REDIRECT_TO_COURSEWARE_MICROFRONTEND.is_enabled(self.course_key):
            return False
        # STAY: If the user has made it past all the above, they're good to stay!
        return True

    @property
    def enrollment(self):
        """
        Return enrollment information.
        """
        if self.effective_user.is_anonymous:
            mode = None
            is_active = False
        else:
            mode, is_active = CourseEnrollment.enrollment_mode_for_user(
                self.effective_user,
                self.course_key
            )
        return {'mode': mode, 'is_active': is_active}

    @property
    def course_expired_message(self):
        # TODO: TNL-7185 Legacy: Refactor to return the expiration date and format the message in the MFE
        return generate_course_expired_message(self.effective_user, self.overview)

    @property
    def offer_html(self):
        # TODO: TNL-7185 Legacy: Refactor to return the offer data and format the message in the MFE
        return generate_offer_html(self.effective_user, self.overview)

    @property
    def content_type_gating_enabled(self):
        return ContentTypeGatingConfig.enabled_for_enrollment(
            user=self.effective_user,
            course_key=self.course_key,
        )

    @property
    def can_show_upgrade_sock(self):
        return (DISPLAY_COURSE_SOCK_FLAG.is_enabled(self.course_key) and
                can_show_verified_upgrade(self.effective_user, self.enrollment_object))

    @property
    def license(self):
        course = get_course_by_id(self.course_key)
        return course.license

    @property
    def can_load_courseware(self):
        access_response = check_course_access(
            self.overview,
            self.effective_user,
            'load',
            check_if_enrolled=True,
            check_survey_complete=False,
            check_if_authenticated=True,
        ).to_json()
        # Only check whether the MFE is enabled if the user would otherwise be allowed to see it
        # This means that if the user was denied access, they'll see a meaningful message first if
        # there is one.
        if access_response and not self.is_microfrontend_enabled_for_user():
            return CoursewareMicrofrontendDisabledAccessError().to_json()
        return access_response

    @property
    def tabs(self):
        """
        Return course tab metadata.
        """
        tabs = []
        for priority, tab in enumerate(get_course_tab_list(self.effective_user, self.overview)):
            tabs.append({
                'title': tab.title or tab.get('name', ''),
                'slug': tab.tab_id,
                'priority': priority,
                'type': tab.type,
                'url': tab.link_func(self.overview, reverse),
            })
        return tabs

    @property
    def verified_mode(self):
        """
        Return verified mode information, or None.
        """
        mode = CourseMode.verified_mode_for_course(self.course_key)
        if mode:
            return {
                'price': mode.min_price,
                'currency': mode.currency.upper(),
                'currency_symbol': get_currency_symbol(mode.currency.upper()),
                'sku': mode.sku,
                'upgrade_url': verified_upgrade_deadline_link(self.effective_user, self.overview),
            }

    @property
    def notes(self):
        """
        Return whether edxnotes is enabled and visible.
        """
        return {
            'enabled': is_feature_enabled(self.overview, self.effective_user),
            'visible': self.overview.edxnotes_visibility,
        }

    @property
    def celebrations(self):
        """
        Returns a list of celebrations that should be performed.
        """
        return {
            'first_section': CourseEnrollmentCelebration.should_celebrate_first_section(self.enrollment_object),
        }


class CoursewareInformation(RetrieveAPIView):
    """
    **Use Cases**

        Request details for a course

    **Example Requests**

        GET /api/courseware/course/{course_key}

    **Response Values**

        Body consists of the following fields:

        * effort: A textual description of the weekly hours of effort expected
            in the course.
        * end: Date the course ends, in ISO 8601 notation
        * enrollment_end: Date enrollment ends, in ISO 8601 notation
        * enrollment_start: Date enrollment begins, in ISO 8601 notation
        * id: A unique identifier of the course; a serialized representation
            of the opaque key identifying the course.
        * media: An object that contains named media items.  Included here:
            * course_image: An image to show for the course.  Represented
              as an object with the following fields:
                * uri: The location of the image
        * name: Name of the course
        * number: Catalog number of the course
        * org: Name of the organization that owns the course
        * short_description: A textual description of the course
        * start: Date the course begins, in ISO 8601 notation
        * start_display: Readably formatted start of the course
        * start_type: Hint describing how `start_display` is set. One of:
            * `"string"`: manually set by the course author
            * `"timestamp"`: generated from the `start` timestamp
            * `"empty"`: no start date is specified
        * pacing: Course pacing. Possible values: instructor, self
        * tabs: Course tabs
        * enrollment: Enrollment status of authenticated user
            * mode: `audit`, `verified`, etc
            * is_active: boolean
        * can_load_course: Whether the user can view the course (AccessResponse object)
        * is_staff: Whether the effective user has staff access to the course
        * original_user_is_staff: Whether the original user has staff access to the course

    **Parameters:**

        requested_fields (optional) comma separated list:
            If set, then only those fields will be returned.
        username (optional) username to masquerade as (if requesting user is staff)

    **Returns**

        * 200 on success with above fields.
        * 400 if an invalid parameter was sent or the username was not provided
          for an authenticated request.
        * 403 if a user who does not have permission to masquerade as
          another user specifies a username other than their own.
        * 404 if the course is not available or cannot be seen.
    """

    authentication_classes = (
        JwtAuthentication,
        SessionAuthenticationAllowInactiveUser,
    )

    serializer_class = CourseInfoSerializer

    def get_object(self):
        """
        Return the requested course object, if the user has appropriate
        permissions.
        """
        if self.request.user.is_staff:
            username = self.request.GET.get('username', '') or self.request.user.username
        else:
            username = self.request.user.username
        overview = CoursewareMeta(
            CourseKey.from_string(self.kwargs['course_key_string']),
            self.request,
            username=username,
        )

        return overview

    def get_serializer_context(self):
        """
        Return extra context to be used by the serializer class.
        """
        context = super().get_serializer_context()
        context['requested_fields'] = self.request.GET.get('requested_fields', None)
        return context


class SequenceMetadata(DeveloperErrorViewMixin, APIView):
    """
    **Use Cases**

        Request details for a sequence/subsection

    **Example Requests**

        GET /api/courseware/sequence/{usage_key}

    **Response Values**

        Body consists of the following fields:
            TODO

    **Returns**

        * 200 on success with above fields.
        * 400 if an invalid parameter was sent.
        * 403 if a user who does not have permission to masquerade as
          another user specifies a username other than their own.
        * 404 if the course is not available or cannot be seen.
    """

    authentication_classes = (
        JwtAuthentication,
        SessionAuthenticationAllowInactiveUser,
    )

    def get(self, request, usage_key_string, *args, **kwargs):
        """
        Return response to a GET request.
        """
        try:
            usage_key = UsageKey.from_string(usage_key_string)
        except InvalidKeyError:
            raise NotFound("Invalid usage key: '{}'.".format(usage_key_string))

        sequence, _ = get_module_by_usage_id(
            self.request,
            str(usage_key.course_key),
            str(usage_key),
            disable_staff_debug_info=True)
        return Response(json.loads(sequence.handle_ajax('metadata', None)))


class Resume(DeveloperErrorViewMixin, APIView):
    """
    **Use Cases**

        Request the last completed block in a course

    **Example Requests**

        GET /api/courseware/resume/{course_key}

    **Response Values**

        Body consists of the following fields:

            * block: the last completed block key
            * section: the key to the section
            * unit: the key to the unit
        If no completion data is available, the keys will be null

    **Returns**

        * 200 on success with above fields.
        * 400 if an invalid parameter was sent.
        * 403 if a user who does not have permission to masquerade as
          another user specifies a username other than their own.
        * 404 if the course is not available or cannot be seen.
    """

    authentication_classes = (
        JwtAuthentication,
        SessionAuthenticationAllowInactiveUser,
    )
    permission_classes = (IsAuthenticated, )

    def get(self, request, course_key_string, *args, **kwargs):
        """
        Return response to a GET request.
        """
        course_id = CourseKey.from_string(course_key_string)
        resp = {
            'block_id': None,
            'section_id': None,
            'unit_id': None,
        }

        try:
            block_key = get_key_to_last_completed_block(request.user, course_id)
            path = path_to_location(modulestore(), block_key, request, full_path=True)
            resp['section_id'] = str(path[2])
            resp['unit_id'] = str(path[3])
            resp['block_id'] = str(block_key)

        except UnavailableCompletionData:
            pass

        return Response(resp)


class Celebration(DeveloperErrorViewMixin, APIView):
    """
    **Use Cases**

        Marks a particular celebration as complete

    **Example Requests**

        POST /api/courseware/celebration/{course_key}

    **Request Parameters**

        Body consists of the following fields:

            * first_section (bool): whether we should celebrate when a user finishes their first section of a course

    **Returns**

        * 200 or 201 or 202 on success with above fields.
        * 400 if an invalid parameter was sent.
        * 404 if the course is not available or cannot be seen.
    """

    authentication_classes = (
        JwtAuthentication,
        SessionAuthenticationAllowInactiveUser,
    )
    permission_classes = (IsAuthenticated, )
    http_method_names = ['post']

    def post(self, request, course_key_string, *args, **kwargs):
        """
        Handle a POST request.
        """
        course_key = CourseKey.from_string(course_key_string)

        # Check if we're masquerading as someone else. If so, we should just ignore this request.
        _, user = setup_masquerade(
            request,
            course_key,
            staff_access=has_access(request.user, 'staff', course_key),
            reset_masquerade_data=True,
        )
        if user != request.user:
            return Response(status=202)  # "Accepted"

        data = dict(request.data)
        first_section = data.pop('first_section', None)
        if data:
            return Response(status=400)  # there were parameters we didn't recognize

        enrollment = CourseEnrollment.get_enrollment(request.user, course_key)
        if not enrollment:
            return Response(status=404)

        defaults = {}
        if first_section is not None:
            defaults['celebrate_first_section'] = first_section

        if defaults:
            _, created = CourseEnrollmentCelebration.objects.update_or_create(enrollment=enrollment, defaults=defaults)
            return Response(status=201 if created else 200)
        else:
            return Response(status=200)  # just silently allow it
