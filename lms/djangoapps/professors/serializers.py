# -*- coding:utf-8 -*-
"""
Professors Serialziers
"""
from __future__ import unicode_literals

import logging
from django.conf import settings
from urlparse import urljoin
from django.urls import reverse
from rest_framework import serializers

from professors.models import Professor, ProfessorCourses
log = logging.getLogger(__name__)


class ProfessorsListSerializer(serializers.ModelSerializer):

    class Meta:
        model = Professor
        fields = ('id', 'user_id', 'name', 'description', 'avatar')


class ProfessorDetailSerializer(serializers.ModelSerializer):
    professor_info = serializers.SerializerMethodField()

    def get_professor_info(self, info):
        professor_info = info.info.replace("\r\n", "").replace('\"', "'")
        return professor_info

    class Meta:
        model = Professor
        fields = ('id', 'user_id', 'name', 'description', 'avatar', 'professor_info')


class ProfessorCoursesListSerializer(serializers.ModelSerializer):
    course_id = serializers.SerializerMethodField()
    course_name = serializers.SerializerMethodField()
    course_image_url = serializers.SerializerMethodField()
    course_about = serializers.SerializerMethodField()

    def get_course_id(self, info):
        return str(info.course_id)

    def get_course_name(self, info):
        return str(info.course.display_name)

    def get_course_image_url(self, info):
        return urljoin(settings.LMS_ROOT_URL, str(info.course.course_image_url))

    def get_course_about(self, info):
        return reverse('about_course', args=[str(info.course_id)])

    class Meta:
        model = ProfessorCourses
        fields = ('id', 'professor', 'course_id', 'course_name', 'course_image_url', 'course_about')


class CourseProfessorSerializer(serializers.ModelSerializer):
    course_id = serializers.SerializerMethodField()

    def get_course_id(self, info):
        return str(info.course_id)

    class Meta:
        model = ProfessorCourses
        fields = ('course_id', 'professor_id')
