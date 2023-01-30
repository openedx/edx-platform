from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import serializers

from openedx.features.genplus_features.genplus.models import Student
from openedx.features.genplus_features.genplus.models import Class
from openedx.features.genplus_features.genplus_assessments.models import (
    UserResponse,
    UserRating
)
from openedx.features.genplus_features.genplus_learning.models import (
    ClassLesson,
    ClassUnit
)


# TODO: remove this serializer
class ClassLessonSerializer(serializers.ModelSerializer):

    class Meta:
        model = ClassLesson
        fields = ('id', 'display_name', 'lms_url', 'usage_key')


# TODO: remove this serializer
class ClassUnitSerializer(serializers.ModelSerializer):
    class_lessons = ClassLessonSerializer(many=True, read_only=True)
    display_name = serializers.CharField(source="unit.display_name")

    class Meta:
        model = ClassUnit
        fields = ('id', 'display_name', 'course_key', 'class_lessons')


class ClassStudentSerializer(serializers.ModelSerializer):
    user_id = serializers.CharField(source='gen_user.user.id', default=None)
    username = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    profile_pic_url = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = ('id', 'user_id', 'username', 'full_name', 'profile_pic_url')

    def get_username(self, obj):
        return obj.gen_user.user.email if obj.gen_user.user else obj.gen_user.email

    def get_full_name(self, obj):
        return obj.gen_user.user.get_full_name() if obj.gen_user.user else ''

    def get_profile_pic_url(self, obj):
        if obj.character is not None and obj.character.profile_pic is not None:
            return f"{settings.LMS_ROOT_URL}{obj.character.profile_pic.url}"
        else:
            return None


# TODO: remove this serializer
class ClassSerializer(serializers.ModelSerializer):
    students = serializers.SerializerMethodField()
    class_units = ClassUnitSerializer(many=True, read_only=True)

    class Meta:
        model = Class
        fields = ('group_id', 'name', 'students', 'class_units')

    def get_students(self, instance):
        students = instance.students.exclude(gen_user__user__isnull=True)
        return ClassStudentSerializer(students, many=True, read_only=True).data


class TextAssessmentSerializer(serializers.ModelSerializer):
    skill = serializers.CharField(source='skill.name')
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = UserResponse
        fields = ('user', 'course_id', 'usage_id', 'problem_id',
                  'assessment_time', 'skill', 'full_name', 'student_response', 'score')

    def get_full_name(self, obj):
        return get_user_model().objects.get(pk=obj.user_id).get_full_name()


class RatingAssessmentSerializer(serializers.ModelSerializer):
    skill = serializers.CharField(source='skill.name')
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = UserRating
        fields = ('user', 'course_id', 'usage_id', 'problem_id',
                  'assessment_time', 'skill', 'full_name', 'rating')

    def get_full_name(self, obj):
        return get_user_model().objects.get(pk=obj.user_id).get_full_name()
