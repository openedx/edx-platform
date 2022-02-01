# pylint: disable=abstract-method
"""
Course Home Serializers.
"""

from opaque_keys.edx.keys import CourseKey
from rest_framework import serializers

from lms.djangoapps.courseware.utils import verified_upgrade_deadline_link
from openedx.core.djangoapps.courseware_api.utils import serialize_upgrade_info
from openedx.features.content_type_gating.models import ContentTypeGatingConfig
from openedx.features.course_experience import DISPLAY_COURSE_SOCK_FLAG
from openedx.features.course_experience.utils import dates_banner_should_display


class ReadOnlySerializer(serializers.Serializer):
    """Serializers have an abstract create & update, but we often don't need them. So this silences the linter."""
    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


class DatesBannerSerializer(ReadOnlySerializer):
    """
    Serializer Mixin for displaying the dates banner.
    Can be added to any serializer who's tab wants to display it.
    """
    dates_banner_info = serializers.SerializerMethodField()

    def get_dates_banner_info(self, _):
        """
        Serializer mixin for returning date banner info.  Gets its input from
        the views course_key_string url parameter and the request's user object.
        """
        info = {
            'missed_deadlines': False,
            'content_type_gating_enabled': False,
        }
        course_key_string = self.context['view'].kwargs.get('course_key_string')
        if course_key_string:
            course_key = CourseKey.from_string(course_key_string)
            request = self.context['request']
            missed_deadlines, missed_gated_content = dates_banner_should_display(course_key, request.user)
            info['missed_deadlines'] = missed_deadlines
            info['missed_gated_content'] = missed_gated_content
            info['content_type_gating_enabled'] = ContentTypeGatingConfig.enabled_for_enrollment(
                user=request.user,
                course_key=course_key,
            )
            info['verified_upgrade_link'] = verified_upgrade_deadline_link(request.user, course_id=course_key)
        return info


class VerifiedModeSerializer(ReadOnlySerializer):
    """
    Serializer Mixin for displaying verified mode upgrade information.

    Requires 'course_overview', 'enrollment', and 'request' from self.context.
    """
    can_show_upgrade_sock = serializers.SerializerMethodField()
    verified_mode = serializers.SerializerMethodField()

    def get_can_show_upgrade_sock(self, _):
        course_overview = self.context['course_overview']
        return DISPLAY_COURSE_SOCK_FLAG.is_enabled(course_overview.id)

    def get_verified_mode(self, _):
        """Return verified mode information, or None."""
        course_overview = self.context['course_overview']
        enrollment = self.context['enrollment']
        request = self.context['request']
        return serialize_upgrade_info(request.user, course_overview, enrollment)
