"""
Serializers for use in the support app.
"""

from datetime import datetime

import pytz
from rest_framework import serializers

from lms.djangoapps.courseware.courses import get_cms_course_link
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview


class CourseTeamManageSerializer(serializers.ModelSerializer):
    """Serializer for course team management context data"""

    role = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    course_url = serializers.SerializerMethodField()

    class Meta:
        model = CourseOverview
        fields = ("id", "display_name", "role", "status", "course_url")

    def get_role(self, obj):
        course_role_map = self.context.get("course_role_map", {})
        return course_role_map.get(str(obj.id))

    def get_status(self, obj):
        """
        Determine if the course is active or archived based on end date.
        Returns 'active' if course end is null or in the future, 'archived' otherwise.
        """
        if obj.end is None or obj.end >= datetime.now().replace(tzinfo=pytz.UTC):
            return "active"
        return "archived"

    def get_course_url(self, obj):
        """
        Construct the course URL for CMS using get_cms_course_link.
        """
        return get_cms_course_link(obj, "course")

    def to_representation(self, instance):
        data = super().to_representation(instance)
        course_key = instance.id
        return {
            "course_id": str(course_key),
            "course_name": data["display_name"],
            "course_url": data["course_url"],
            "role": data["role"],
            "status": data["status"],
            "org": course_key.org,
            "run": course_key.run,
            "number": course_key.course,
        }
