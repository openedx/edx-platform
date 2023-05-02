"""
Serializers for the notifications API.
"""
from rest_framework import serializers

from common.djangoapps.student.models import CourseEnrollment
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview


class CourseOverviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseOverview
        fields = ('id', 'display_name')


class CourseEnrollmentSerializer(serializers.ModelSerializer):
    course = CourseOverviewSerializer()

    class Meta:
        model = CourseEnrollment
        fields = ('course', 'is_active', 'mode')
