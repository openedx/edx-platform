from rest_framework import serializers
from openedx.features.genplus_features.genplus.models import Character, Skill


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ('name', )


class CharacterSerializer(serializers.ModelSerializer):
    skills = SkillSerializer(read_only=True, many=True)

    class Meta:
        model = Character
        fields = '__all__'
