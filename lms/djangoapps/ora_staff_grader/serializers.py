"""
Serializers for Enhanced Staff Grader (ESG)
"""
# pylint: disable=abstract-method

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
    pointsEarned = serializers.IntegerField(default=0)
    pointsPossible = serializers.IntegerField(default=0)

    class Meta:
        fields = ['pointsEarned', 'pointsPossible']

    def to_representation(self, instance):
        """ An empty dict should return None instead """
        if ('pointsEarned' not in instance) and ('pointsPossible' not in instance):
            return None
        return super().to_representation(instance)


class SubmissionMetadataSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """
    Submission metadata for displaying submissions table in ESG
    """
    submissionUuid = serializers.CharField()
    username = serializers.CharField(allow_null=True)
    teamName = serializers.CharField(allow_null=True)
    dateSubmitted = serializers.DateTimeField()
    dateGraded = serializers.DateTimeField(allow_null=True)
    gradedBy = serializers.CharField(allow_null=True)
    gradingStatus = serializers.CharField()
    lockStatus = serializers.CharField()
    score = ScoreSerializer(allow_null=True)

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


class InitializeSerializer(serializers.Serializer):
    """
    Serialize info for the initialize call. Packages ORA, course, submission, and rubric data.
    """
    courseMetadata = CourseMetadataSerializer()
    oraMetadata = OpenResponseMetadataSerializer()
    submissions = serializers.DictField(child=SubmissionMetadataSerializer())
    rubricConfig = serializers.DictField()

    class Meta:
        fields = [
            'courseMetadata',
            'oraMetadata',
            'submissions',
            'rubricConfig',
        ]
