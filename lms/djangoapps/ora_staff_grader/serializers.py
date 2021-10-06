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
    type = serializers.SerializerMethodField()

    def get_type(self, instance):
        return 'team' if instance.teams_enabled else 'individual'

    class Meta:
        fields = [
            'name',
            'prompts',
            'type',
        ]


class ScoreSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """
    Score (points earned/possible) for use in SubmissionMetadataSerializer
    """
    pointsEarned = serializers.IntegerField()
    pointsPossible = serializers.IntegerField()

    class Meta:
        fields = ['pointsEarned', 'pointsPossible']


class SubmissionMetadataSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """
    Submission metadata for displaying submissions table in ESG
    """
    submissionUuid = serializers.CharField()
    username = serializers.CharField()
    teamName = serializers.CharField()
    dateSubmitted = serializers.DateTimeField()
    dateGraded = serializers.DateTimeField()
    gradedBy = serializers.CharField()
    gradingStatus = serializers.CharField()
    lockStatus = serializers.CharField()
    score = ScoreSerializer()

    class Meta:
        fields = [
            'submissionUuid',
            'username',
            'teamName',
            'dateSubmitted',
            'dateGraded',
            'gradedBy',
            'gradingStatus',
            'lockStatus',
            'score'
        ]
