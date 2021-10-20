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


class InitializeSerializer(serializers.Serializer):
    courseMetadata = CourseMetadataSerializer()
    oraMetadata = OpenResponseMetadataSerializer()
    submissions = serializers.DictField()
    rubricConfig = serializers.DictField()

    class Meta:
        fields = [
            'courseMetadata',
            'oraMetadata',
            'submissions',
            'rubricConfig',
        ]

    @staticmethod
    def transform_submission(submission):
        """ Basic data transforms for submissions """

        # Add teamName if omitted, this is allowed for individual responses
        if 'teamName' not in submission:
            submission['teamName'] = None

        # Add username if omitted, this is allowed for team responses
        if 'username' not in submission:
            submission['username'] = None

        # An empty score dict should be transformed to None
        if not submission['score']:
            submission['score'] = None

        return submission

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        # Some basic transforms/cleanup for Submissions
        for (submission_id, submission) in representation['submissions'].items():
            representation['submissions'][submission_id] = self.transform_submission(submission)

        return representation
