# pylint: disable=abstract-method
"""
Course Home Mixins.
"""


from rest_framework import serializers

from opaque_keys.edx.keys import CourseKey

from lms.djangoapps.courseware.date_summary import verified_upgrade_deadline_link
from openedx.features.content_type_gating.models import ContentTypeGatingConfig
from openedx.features.course_experience.utils import dates_banner_should_display


class DatesBannerSerializerMixin(serializers.Serializer):
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
