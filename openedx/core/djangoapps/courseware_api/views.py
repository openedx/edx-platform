"""
Course API Views
"""

import json

from babel.numbers import get_currency_symbol
from completion.exceptions import UnavailableCompletionData
from completion.utilities import get_key_to_last_completed_block
from django.urls import reverse
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from opaque_keys.edx.keys import CourseKey, UsageKey
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from course_modes.models import CourseMode
from edxnotes.helpers import is_feature_enabled
from lms.djangoapps.course_api.api import course_detail
from lms.djangoapps.courseware.access import has_access
from lms.djangoapps.courseware.courses import check_course_access
from lms.djangoapps.courseware.module_render import get_module_by_usage_id
from lms.djangoapps.courseware.tabs import get_course_tab_list
from lms.djangoapps.courseware.utils import can_show_verified_upgrade
from lms.djangoapps.courseware.utils import verified_upgrade_deadline_link
from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin
from openedx.features.content_type_gating.models import ContentTypeGatingConfig
from openedx.features.course_duration_limits.access import generate_course_expired_message
from openedx.features.discounts.utils import generate_offer_html
from student.models import CourseEnrollment
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
        self.course_key = course_key

    def __getattr__(self, name):
        return getattr(self.overview, name)

    @property
    def is_staff(self):
        return has_access(self.effective_user, 'staff', self.overview).has_access

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
        enrollment = CourseEnrollment.get_enrollment(self.effective_user, self.course_key)
        can_show = can_show_verified_upgrade(self.effective_user, enrollment)
        return can_show

    @property
    def can_load_courseware(self):
        return check_course_access(
            self.overview,
            self.effective_user,
            'load',
            check_if_enrolled=True,
            check_survey_complete=False,
            check_if_authenticated=True,
        ).to_json()

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
        * is_staff: Whether the user has staff access to the course

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
        usage_key = UsageKey.from_string(usage_key_string)

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
