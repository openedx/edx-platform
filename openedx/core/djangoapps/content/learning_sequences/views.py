"""
The views.py for this app is intentionally thin, and only exists to translate
user input/output to and from the business logic in the `api` package.
"""
from datetime import datetime, timezone
import json
import logging

from django.contrib.auth import get_user_model
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers
import attr

from openedx.core.lib.api.permissions import IsStaff
from .api import get_user_course_outline_details

User = get_user_model()
log = logging.getLogger(__name__)


class CourseOutlineView(APIView):
    """
    Display all CourseOutline information for a given user.
    """
    # We want to eventually allow unauthenticated users to use this as well...
    authentication_classes = (JwtAuthentication, SessionAuthenticationAllowInactiveUser)

    # For early testing, restrict this to only global staff...
    permission_classes = (IsStaff,)

    class UserCourseOutlineDataSerializer(serializers.BaseSerializer):
        """
        Read-only serializer for CourseOutlineData for this endpoint.

        This serializer was purposefully declared inline with the
        CourseOutlineView to discourage reuse/magic. Our goal is to make it
        extremely obvious how things are being serialized, and not have surprise
        regressions because a shared serializer in another module was modified
        to fix an issue in one of its three use cases.

        The data structures in api/data.py send back try to separate the data by
        lifecycle (e.g. CourseOutlineData vs UserCourseOutlineData) and by
        logical system (e.g. ScheduleData) to promote performance and
        pluggability. But for the REST API, we're just trying to collapse those
        into the simplest, most convenient output possible.

        We also remove any references to "usage_keys" at this layer. UsageKeys
        are a critical part of the internals of edx-platform, so the in-process
        API uses them, but we translate them to "ids" for REST API clients.
        """
        def to_representation(self, user_course_outline_details):
            """
            Convert to something DRF knows how to serialize (so no custom types)

            This is intentionally dumb and lists out every field to make API
            additions/changes more obvious.
            """
            user_course_outline = user_course_outline_details.outline
            schedule = user_course_outline_details.schedule
            return {
                # Top level course information
                "course_key": str(user_course_outline.course_key),
                "course_start": schedule.course_start,
                "course_end": schedule.course_end,
                "title": user_course_outline.title,
                "published_at": user_course_outline.published_at,
                "published_version": user_course_outline.published_version,
                "days_early_for_beta": user_course_outline.days_early_for_beta,
                "self_paced": user_course_outline.self_paced,

                # Who and when this request was generated for (we can eventually
                # support arbitrary times).
                "username": user_course_outline.user.username,  # "" if anonymous
                "user_id": user_course_outline.user.id,  # null if anonymous
                "at_time": user_course_outline.at_time,

                # The actual course structure information...
                "outline": {
                    "sections": [
                        self._section_repr(section, schedule.sections.get(section.usage_key))
                        for section in user_course_outline.sections
                    ],
                    "sequences": {
                        str(seq_usage_key): self._sequence_repr(
                            sequence,
                            schedule.sequences.get(seq_usage_key),
                            user_course_outline.accessible_sequences,
                        )
                        for seq_usage_key, sequence in user_course_outline.sequences.items()
                    },
                },
            }

        def _sequence_repr(self, sequence, sequence_schedule, accessible_sequences):
            """Representation of a Sequence."""
            if sequence_schedule is None:
                schedule_item_dict = {'start': None, 'effective_start': None, 'due': None}
            else:
                schedule_item_dict = {
                    # Any of these values could be `None`
                    'start': sequence_schedule.start,
                    'effective_start': sequence_schedule.effective_start,
                    'due': sequence_schedule.due,
                }

            return {
                "id": str(sequence.usage_key),
                "title": sequence.title,
                "accessible": sequence.usage_key in accessible_sequences,
                "inaccessible_after_due": sequence.inaccessible_after_due,
                **schedule_item_dict,
            }

        def _section_repr(self, section, section_schedule):
            """Representation of a Section."""
            if section_schedule is None:
                schedule_item_dict = {'start': None, 'effective_start': None}
            else:
                # Scheduling data is very similiar to Sequences, but there are
                # no due dates for Sections. It's in the data model because OLX
                # lets you put it there, but that's a quirk that API clients
                # shouldn't have to care about.
                schedule_item_dict = {
                    # Any of these values could be `None`
                    'start': section_schedule.start,
                    'effective_start': section_schedule.effective_start,
                }

            return {
                "id": str(section.usage_key),
                "title": section.title,
                "sequence_ids": [
                    str(seq.usage_key) for seq in section.sequences
                ],
                **schedule_item_dict,
            }

    def get(self, request, course_key_str, format=None):
        """
        The CourseOutline, customized for a given user.

        Currently restricted to global staff.

        TODO: Swagger docs of API. For an exemplar to imitate, see:
        https://github.com/edx/edx-platform/blob/master/lms/djangoapps/program_enrollments/rest_api/v1/views.py#L792-L820
        """
        # Translate input params and do any substitutions...
        course_key = self._validate_course_key(course_key_str)
        at_time = datetime.now(timezone.utc)
        user = self._determine_user(request)

        # Grab the user's outline and send our response...
        user_course_outline_details = get_user_course_outline_details(course_key, user, at_time)
        serializer = self.UserCourseOutlineDataSerializer(user_course_outline_details)
        return Response(serializer.data)

    def _validate_course_key(self, course_key_str):
        try:
            course_key = CourseKey.from_string(course_key_str)
        except InvalidKeyError:
            raise serializers.ValidationError(
                "{} is not a valid CourseKey".format(course_key_str)
            )
        if course_key.deprecated:
            raise serializers.ValidationError(
                "Deprecated CourseKeys (Org/Course/Run) are not supported."
            )
        return course_key

    def _determine_user(self, request):
        """
        Requesting for a different user (easiest way to test for students)
        while restricting access to only global staff. This is a placeholder
        until we have more full fledged permissions/masquerading.
        """
        requested_username = request.GET.get("user")
        if request.user.is_staff and requested_username:
            return User.objects.get(username=requested_username)

        return request.user
