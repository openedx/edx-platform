from rest_framework import serializers
from openedx.features.genplus_features.genplus.models import Character, Skill, Class
from openedx.features.genplus_features.genplus.display_messages import ErrorMessages


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
