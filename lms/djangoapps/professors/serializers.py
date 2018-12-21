# -*- coding:utf-8 -*-
"""
Professors Serialziers
"""

from __future__ import unicode_literals
from rest_framework import serializers

from professors.models import Professor


class ProfessorsListSerializer(serializers.ModelSerializer):

    class Meta:
        model = Professor
        fields = ('id', 'user_id', 'name', 'description', 'avatar')


class ProfessorDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = Professor
        fields = ('id', 'user_id', 'name', 'description', 'avatar', 'slogan', 'introduction',
                  'main_achievements', 'education_experience', 'other_achievements',
                  'research_fields', 'research_papers', 'project_experience')
