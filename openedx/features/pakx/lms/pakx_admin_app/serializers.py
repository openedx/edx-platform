"""
Serializer for Admin Panel APIs
"""
from django.contrib.auth.models import User
from rest_framework import serializers

from student.models import CourseEnrollment, UserProfile

from .constants import GROUP_TRAINING_MANAGERS, LEARNER, ORG_ADMIN, TRAINING_MANAGER


class UserCourseEnrollmentSerializer(serializers.ModelSerializer):
    """
    Serializer for list API of user course enrollment
    """
    course_id = serializers.CharField(source='course.id')
    display_name = serializers.CharField(source='course.display_name')
    enrollment_status = serializers.CharField(source='mode')
    enrollment_date = serializers.SerializerMethodField()
    completion_date = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()
    grades = serializers.SerializerMethodField()

    class Meta:
        model = CourseEnrollment
        fields = (
            'course_id', 'display_name', 'enrollment_status', 'enrollment_date',
            'progress', 'completion_date', 'grades'
        )

    @staticmethod
    def get_enrollment_date(obj):
        return obj.created.strftime('%Y-%m-%d')

    @staticmethod
    def get_progress(obj):
        return obj.enrollment_stats.progress if obj.enrollment_stats else None

    @staticmethod
    def get_completion_date(obj):
        return obj.enrollment_stats.completion_date if obj.enrollment_stats else None

    @staticmethod
    def get_grades(obj):
        return obj.enrollment_stats.grade if obj.enrollment_stats else None


class UserDetailViewSerializer(serializers.ModelSerializer):
    """
    Serializer User's object retrieve view
    """
    employee_id = serializers.CharField(source='profile.employee_id')
    name = serializers.CharField(source='profile.name')
    course_enrolled = serializers.SerializerMethodField()
    completed_courses = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'email', 'name', 'employee_id', 'is_active', 'date_joined', 'last_login', 'course_enrolled',
                  'completed_courses')

    @staticmethod
    def get_course_enrolled(obj):
        return obj.completed + obj.in_prog

    @staticmethod
    def get_completed_courses(obj):
        return obj.completed


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer User's view-set list view
    """
    employee_id = serializers.CharField(source='profile.employee_id')
    language = serializers.CharField(source='profile.language')
    name = serializers.CharField(source='profile.name')
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('username', 'id', 'email', 'name', 'employee_id', 'language', 'is_active', 'role')

    @staticmethod
    def get_role(obj):
        if obj.staff_groups:
            return TRAINING_MANAGER if obj.staff_groups[0].name == GROUP_TRAINING_MANAGERS else ORG_ADMIN

        return LEARNER


class BasicUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ('user', 'employee_id', 'language', 'organization')


class LearnersSerializer(serializers.ModelSerializer):
    """
    Serializer Learner list view for analytics view list view
    """
    name = serializers.CharField(source='profile.name')
    assigned_courses = serializers.SerializerMethodField()
    incomplete_courses = serializers.SerializerMethodField()
    completed_courses = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'name', 'email', 'last_login', 'assigned_courses', 'incomplete_courses', 'completed_courses')

    @staticmethod
    def get_assigned_courses(obj):
        return len(obj.enrollment)

    @staticmethod
    def get_incomplete_courses(obj):

        return len([stat for stat in obj.enrollment if stat.enrollment_stats.progress < 100])

    @staticmethod
    def get_completed_courses(obj):
        return len([stat for stat in obj.enrollment if stat.enrollment_stats.progress == 100])
