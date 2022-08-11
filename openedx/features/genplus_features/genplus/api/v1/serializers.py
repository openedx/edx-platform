from django.conf import settings
from django.middleware import csrf
from rest_framework import serializers
from common.djangoapps.student.models import UserProfile
from openedx.features.genplus_features.genplus.models import Teacher, Character, Skill, Class, JournalPost
from openedx.features.genplus_features.genplus.display_messages import ErrorMessages
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
    name = serializers.SerializerMethodField()
    class Meta:
        model = Teacher
        fields = ('id', 'name', 'profile_image')

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


class ClassSerializer(serializers.ModelSerializer):
    current_unit = serializers.SerializerMethodField('get_current_unit')
    lesson = serializers.SerializerMethodField('get_lesson')

    def get_current_unit(self, instance):
        return 'Current Unit'

    def get_lesson(self, instance):
        return 'Lesson'

    class Meta:
        model = Class
        fields = ('group_id', 'name', 'current_unit', 'lesson')


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
    created = serializers.DateTimeField(format="%d/%m/%Y")
    class Meta:
        model = JournalPost
        fields = ('title', 'skill', 'description', 'teacher', 'type', 'created')


class StudentPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = JournalPost
        fields = ('student', 'title', 'skill', 'description', 'type')
        extra_kwargs = {'skill': {'required': True, 'allow_null': False}}


class TeacherFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = JournalPost
        fields = ('teacher', 'student', 'title', 'description', 'type')
        extra_kwargs = {'teacher': {'required': True, 'allow_null': False}}
