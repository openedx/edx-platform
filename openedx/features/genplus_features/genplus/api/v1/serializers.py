from django.conf import settings
from django.middleware import csrf
from rest_framework import serializers
from common.djangoapps.student.models import UserProfile
from openedx.features.genplus_features.genplus.models import Teacher, Character, Skill, Class, JournalPost
from openedx.features.genplus_features.common.display_messages import ErrorMessages
from django.contrib.auth import get_user_model


class UserInfoSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='profile.name')
    role = serializers.CharField(source='gen_user.role')
    school = serializers.CharField(source='gen_user.school.name')
    csrf_token = serializers.SerializerMethodField('get_csrf_token')

    def to_representation(self, instance):
        user_info = super(UserInfoSerializer, self).to_representation(instance)
        request = self.context.get('request')
        gen_user = self.context.get('gen_user')
        if instance.gen_user.is_student:
            student_profile = {
                'on_board': gen_user.student.onboarded,
                'has_access_to_lessons': gen_user.student.has_access_to_lessons,
                'character_id': gen_user.student.character.id
                if gen_user.student.character else None,
                'profile_image': request.build_absolute_uri(
                    gen_user.student.character.profile_pic.url)
                if gen_user.student.character else None
            }

            user_info.update(student_profile)
        elif instance.gen_user.is_teacher:
            teacher_profile = {
                'on_board': '',
                'character_id': '',
                'profile_image': request.build_absolute_uri(
                    gen_user.teacher.profile_image.url)
                if gen_user.teacher.profile_image else None
            }

            user_info.update(teacher_profile)
        return user_info


    def get_csrf_token(self, instance):
        return self.context.get('request').COOKIES.get('csrftoken')

    class Meta:
        model = get_user_model()
        fields = ('id', 'name', 'username', 'csrf_token', 'role',
                  'first_name', 'last_name', 'email', 'school')

class TeacherSerializer(serializers.ModelSerializer):
    user_id = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    class Meta:
        model = Teacher
        fields = ('id', 'user_id', 'name', 'profile_image')
    
    def get_user_id(self, obj):
        return obj.gen_user.user.id

    def get_name(self, obj):
        profile = UserProfile.objects.filter(user=obj.gen_user.user).first()
        if profile:
            return profile.name
        return None


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = '__all__'


class CharacterSerializer(serializers.ModelSerializer):
    skills = SkillSerializer(read_only=True, many=True)

    class Meta:
        model = Character
        fields = '__all__'


class ClassListSerializer(serializers.ModelSerializer):
    current_unit = serializers.SerializerMethodField('get_current_unit')
    lesson = serializers.SerializerMethodField('get_lesson')

    def get_current_unit(self, instance):
        return 'Current Unit'

    def get_lesson(self, instance):
        return 'Lesson'

    class Meta:
        model = Class
        fields = ('id', 'name', 'group_id', 'current_unit', 'lesson')


class ClassSummarySerializer(serializers.ModelSerializer):
    school_name = serializers.CharField(source="school.name")
    program_name = serializers.CharField(source="program.year_group.name", default=None)

    class Meta:
        model = Class
        fields = ('group_id', 'name', 'school_name', 'program_name',)


class FavoriteClassSerializer(serializers.Serializer):
    action = serializers.CharField(max_length=32)

    def validate(self, data):
        if data['action'] not in ['add', 'remove']:
            raise serializers.ValidationError(
                ErrorMessages.ACTION_VALIDATION_ERROR
            )
        return data


class JournalListSerializer(serializers.ModelSerializer):
    skill = SkillSerializer(read_only=True)
    teacher = TeacherSerializer(read_only=True)
    class Meta:
        model = JournalPost
        fields = ('id', 'title', 'skill', 'description', 'teacher', 'journal_type', 'created')

class StudentPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = JournalPost
        fields = ('student', 'title', 'skill', 'description', 'journal_type')
        extra_kwargs = {'skill': {'required': True, 'allow_null': False}}


class TeacherFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = JournalPost
        fields = ('teacher', 'student', 'title', 'description', 'journal_type')
        extra_kwargs = {'teacher': {'required': True, 'allow_null': False}}


class ContactSerailizer(serializers.Serializer):
    message = serializers.CharField(required=True)
