"""
API Serializers for course team
"""

from datetime import datetime

import pytz
from rest_framework import serializers

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview


class UserCourseTeamSerializer(serializers.Serializer):
    """Serializer for user in course team"""

    email = serializers.CharField()
    id = serializers.IntegerField()
    role = serializers.CharField()
    username = serializers.CharField()


class CourseTeamSerializer(serializers.Serializer):
    """Serializer for course team context data"""

    show_transfer_ownership_hint = serializers.BooleanField()
    users = UserCourseTeamSerializer(many=True)
    allow_actions = serializers.BooleanField()


class CourseTeamManagementSerializer(serializers.ModelSerializer):
    """Serializer for course team management context data"""

    role = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = CourseOverview
        fields = ("id", "display_name", "role", "status")

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

    def to_representation(self, instance):
        data = super().to_representation(instance)
        course_key = instance.id
        return {
            "course_id": str(course_key),
            "course_name": data["display_name"],
            "role": data["role"],
            "status": data["status"],
            "org": course_key.org,
            "run": course_key.run,
            "number": course_key.course,
        }
