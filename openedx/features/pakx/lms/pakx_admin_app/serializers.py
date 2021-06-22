"""
Serializer for Admin Panel APIs
"""
from django.contrib.auth.models import User
from rest_framework import serializers
from six import text_type

from lms.djangoapps.grades.api import CourseGradeFactory
from openedx.features.pakx.lms.overrides.utils import get_course_progress_percentage
from student.models import CourseEnrollment, UserProfile

from .constants import GROUP_TRAINING_MANAGERS, LEARNER, ORG_ADMIN, TRAINING_MANAGER


class UserCourseEnrollmentSerializer(serializers.ModelSerializer):
    """
    Serializer for list API of user course enrollment
    """
    display_name = serializers.CharField(source='course.display_name')
    enrollment_status = serializers.CharField(source='mode')
    enrollment_date = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()
    grades = serializers.SerializerMethodField()

    class Meta:
        model = CourseEnrollment
        fields = ('display_name', 'enrollment_status', 'enrollment_date', 'progress', 'grades')

    @staticmethod
    def get_enrollment_date(obj):
        return obj.created.strftime('%Y-%m-%d')

    def get_progress(self, obj):
        return get_course_progress_percentage(self.context['request'], text_type(obj.course.id))

    @staticmethod
    def get_grades(obj):
        grades = CourseGradeFactory().read(obj.user, course_key=obj.course.id)
        return {'passed': grades.passed, 'score': grades.percent}


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
        fields = ('username', 'id', 'email', 'name', 'employee_id', 'language', 'is_active', 'role',
                  'date_joined', 'last_login')

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
    name = serializers.CharField(source='get_full_name')
    assigned_courses = serializers.SerializerMethodField()
    incomplete_courses = serializers.SerializerMethodField()
    completed_courses = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'name', 'email', 'last_login', 'assigned_courses', 'incomplete_courses', 'completed_courses')

    @staticmethod
    def get_assigned_courses(obj):
        return len(obj.course_stats)

    @staticmethod
    def get_incomplete_courses(obj):
        return len([stat for stat in obj.course_stats if stat.progress < 100])

    @staticmethod
    def get_completed_courses(obj):
        return len([stat for stat in obj.course_stats if stat.progress == 100])
