"""
Serializer for Admin Panel APIs
"""
from django.contrib.auth.models import User
from rest_framework import serializers

from .constants import GROUP_TRAINING_MANAGERS, LEARNER, ORG_ADMIN, TRAINING_MANAGER


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer User's view-set list view
    """
    employee_id = serializers.CharField(source='profile.employee_id')
    language = serializers.CharField(source='profile.language')
    name = serializers.CharField(source='get_full_name')
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'email', 'name', 'employee_id', 'language', 'is_active', 'role')

    def get_role(self, obj):
        if obj.staff_groups:
            return TRAINING_MANAGER if obj.staff_groups[0].name == GROUP_TRAINING_MANAGERS else ORG_ADMIN

        return LEARNER


class LearnersSerializer(serializers.ModelSerializer):
    """
    Serializer Learner list view for analytics view list view
    """
    name = serializers.CharField(source='get_full_name')
    assigned_courses = serializers.SerializerMethodField()
    incomplete_courses = serializers.SerializerMethodField()
    completed_courses = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'name', 'email', 'last_login', 'assigned_courses', 'incomplete_courses', 'completed_courses')

    def get_assigned_courses(self, obj):
        return len(obj.enrollments)

    def get_incomplete_courses(self, obj):
        # todo: placeholder data, use figure's data for course completion once it's integrated
        return obj.id

    def get_completed_courses(self, obj):
        # todo: placeholder data, use figure's data for course completion once it's integrated
        return obj.id
