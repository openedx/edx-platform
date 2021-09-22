"""
Serializers for Enhanced Staff Grader (ESG)
"""
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from rest_framework import serializers


class CourseMetadataSerializer(serializers.Serializer):
    title = serializers.CharField(source='display_name')
    org = serializers.CharField(source='display_org_with_default')
    number = serializers.CharField(source='display_number_with_default')

    class Meta:
        model = CourseOverview

        fields = [
            'title',
            'org',
            'number',
        ]


class OpenResponseMetadataSerializer(serializers.Serializer):
    pass


class SubmissionsSummarySerializer(serializers.Serializer):
    pass
