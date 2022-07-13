from django.conf import settings
from django.middleware import csrf
from rest_framework import serializers
from openedx.features.genplus_features.genplus.models import Character, Skill, Class
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


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ('name',)


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
