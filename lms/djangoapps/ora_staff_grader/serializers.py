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
    name = serializers.CharField(source='display_name')
    prompts = serializers.ListField()

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['type'] = 'team' if instance.teams_enabled else 'individual'
        return ret

    class Meta:
        fields = [
            'name',
            'prompts',
            'type',
        ]


class GradeDataSerializer(serializers.Serializer):
    pointsEarned = serializers.IntegerField()
    pointsPossible = serializers.IntegerField()

    class Meta:
        fields = [ 'pointsEarned', 'pointsPossible' ]


class SubmissionMetadataSerializer(serializers.Serializer):
    submissionId = serializers.CharField()
    username = serializers.CharField()
    teamName = serializers.CharField()
    dateSubmitted = serializers.DateTimeField()
    gradeStatus = serializers.CharField()
    lockStatus = serializers.CharField()
    grade = GradeDataSerializer()

    class Meta:
        fields = [
            'submissionId',
            'username',
            'teamName',
            'dateSubmitted',
            'gradeStatus',
            'lockStatus',
            'grade'
        ]

