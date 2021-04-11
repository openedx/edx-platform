"""
Serializer for Course Deadlines (Mobile)
"""
from rest_framework import serializers

from opaque_keys.edx.keys import CourseKey

from lms.djangoapps.course_home_api.mixins import DatesBannerSerializerMixin
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview


class CourseDeadlinesMobileSerializer(DatesBannerSerializerMixin):
    has_ended = serializers.SerializerMethodField()

    def get_has_ended(self, _):
        course_key_string = self.context['view'].kwargs.get('course_key_string')
        course_key = CourseKey.from_string(course_key_string)
        course = CourseOverview.get_from_id(course_key)

        return course.has_ended()
