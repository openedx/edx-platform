"""
Serializers for Enhanced Staff Grader (ESG)
"""
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from rest_framework import serializers


class CourseMetadataSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """
    Serialize top-level info about a course, used for creating header in ESG
    """
    title = serializers.CharField(source='display_name')
    org = serializers.CharField(source='display_org_with_default')
    number = serializers.CharField(source='display_number_with_default')
    courseId = serializers.CharField(source='id')

    class Meta:
        model = CourseOverview

        fields = [
            'title',
            'org',
            'number',
            'courseId',
        ]


class OpenResponseMetadataSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """
    Serialize ORA metadata, used for setting up views in ESG
    """
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


class GradeDataSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """
    Grade data shape (points earned/possible) for use in SubmissionMetadataSerializer
    """
    pointsEarned = serializers.IntegerField()
    pointsPossible = serializers.IntegerField()

    class Meta:
        fields = ['pointsEarned', 'pointsPossible']


class SubmissionMetadataSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """
    Submission metadata for displaying submissions table in ESG
    """
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
