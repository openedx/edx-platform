import functools
from django.conf import settings
from django.contrib.auth import get_user_model
from openedx.features.genplus_features.genplus_assessments.constants import SkillReflectionQuestionType
from rest_framework import serializers

from openedx.features.genplus_features.genplus.models import Student
from openedx.features.genplus_features.genplus.models import Class
from openedx.features.genplus_features.genplus_assessments.models import (
    UserResponse,
    UserRating,
    SkillAssessmentQuestion,
    SkillAssessmentResponse
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
        return obj.gen_user.user.profile.name if obj.gen_user.user else ''

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
        return get_user_model().objects.get(pk=obj.user_id).profile.name


class RatingAssessmentSerializer(serializers.ModelSerializer):
    skill = serializers.CharField(source='skill.name')
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = UserRating
        fields = ('user', 'course_id', 'usage_id', 'problem_id',
                  'assessment_time', 'skill', 'full_name', 'rating')

    def get_full_name(self, obj):
        return get_user_model().objects.get(pk=obj.user_id).profile.name

class SkillAssessmentQuestionSerializer(serializers.ModelSerializer):
    skill = serializers.CharField(source='skill.name')

    class Meta:
        model = SkillAssessmentQuestion
        fields = (
            'question_number',
            'start_unit',
            'start_unit_location',
            'end_unit',
            'end_unit_location',
            'skill',
            'problem_type',
        )

class SkillAssessmentResponseSerializer(serializers.ModelSerializer):
    question = SkillAssessmentQuestionSerializer(many=False, read_only=True)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = SkillAssessmentResponse
        fields = ('user', 'question', 'earned_score', 'total_score', 'response_time',
                  'skill_assessment_type', 'question_response', 'full_name')

    def get_full_name(self, obj):
        return get_user_model().objects.get(pk=obj.user_id).profile.name


class SkillReflectionQuestionSerializer(serializers.ModelSerializer):
    submissions = serializers.SerializerMethodField()
    skill = serializers.CharField(source='skill.name')
    program_name = serializers.CharField(source='program.year_group.name')
    problem_type_name = serializers.SerializerMethodField()

    def get_problem_type_name(self, obj: SkillAssessmentQuestion):
        return SkillReflectionQuestionType(obj.problem_type).name

    def get_submissions(self, obj: SkillAssessmentQuestion):
        intro_submissions = obj.submissions.filter(problem_location=obj.start_unit_location).all()
        outro_submissions = obj.submissions.filter(problem_location=obj.end_unit_location).all()
        map_response = lambda i: {
            **i.question_response['student_response'],
            'username': i.user.username,
            'name': i.user.profile.name,
            'sid': i.id
        }

        def reducer(problem_key):
            def func(init, sub):
                return {
                    **init,
                    sub['username']: {
                        problem_key: sub,
                        'name': sub['name'],
                        'username': sub['username']
                    }
                }

            return func

        reduced = functools.reduce(reducer('intro'), list(map(map_response, intro_submissions)), {})
        reduced = functools.reduce(reducer('outro'), list(map(map_response, outro_submissions)), reduced)
        return reduced

    class Meta:
        model = SkillAssessmentQuestion
        fields = '__all__'
