"""
API Serializers for course team
"""

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

    class Meta:
        model = CourseOverview
        fields = ("id", "display_name", "role")

    def get_role(self, obj):
        course_role_map = self.context.get("course_role_map", {})
        return course_role_map.get(str(obj.id))

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return {
            "course_id": data["id"],
            "course_name": data["display_name"],
            "role": data["role"],
        }
