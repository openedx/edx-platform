"""
Serializers for Enhanced Staff Grader (ESG)
"""
# pylint: disable=abstract-method

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from rest_framework import serializers


class GradeStatusField(serializers.ChoiceField):
    """ Field that can have the values ['graded' 'ungraded'] """
    def __init__(self, *args, **kwargs):
        kwargs['choices'] = ['graded', 'ungraded']
        super().__init__(*args, **kwargs)


class LockStatusField(serializers.ChoiceField):
    """ Field that can have the values ['unlocked', 'locked', 'in-progress'] """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, choices=['unlocked', 'locked', 'in-progress'])


class CourseMetadataSerializer(serializers.Serializer):
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
        read_only_fields = fields


class OpenResponseMetadataSerializer(serializers.Serializer):
    """
    Serialize ORA metadata, used for setting up views in ESG
    """
    name = serializers.CharField(source='display_name')
    prompts = serializers.ListField()
    type = serializers.SerializerMethodField()
    textResponseConfig = serializers.SerializerMethodField()
    fileUploadResponseConfig = serializers.SerializerMethodField()

    def get_textResponseConfig(self, instance):
        return instance.text_response or 'none'

    def get_fileUploadResponseConfig(self, instance):
        return instance.file_upload_response or 'none'

    def get_type(self, instance):
        return 'team' if instance.teams_enabled else 'individual'

    class Meta:
        fields = [
            'name',
            'prompts',
            'type',
            'textResponseConfig',
            'fileUploadResponseConfig',
        ]
        read_only_fields = fields


class ScoreField(serializers.Field):
    def to_representation(self, value):
        if ('pointsEarned' not in value) and ('pointsPossible' not in value):
            return None
        return ScoreSerializer(value).data


class ScoreSerializer(serializers.Serializer):
    """
    Score (points earned/possible) for use in SubmissionMetadataSerializer
    """
    pointsEarned = serializers.IntegerField(required=False)
    pointsPossible = serializers.IntegerField(required=False)


class SubmissionMetadataSerializer(serializers.Serializer):
    """
    Submission metadata for displaying submissions table in ESG
    """
    submissionUuid = serializers.CharField()
    username = serializers.CharField(allow_null=True)
    teamName = serializers.CharField(allow_null=True)
    dateSubmitted = serializers.DateTimeField()
    dateGraded = serializers.DateTimeField(allow_null=True)
    gradedBy = serializers.CharField(allow_null=True)
    gradingStatus = GradeStatusField()
    lockStatus = LockStatusField()
    score = ScoreField()

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
        read_only_fields = fields


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
        read_only_fields = fields


class UploadedFileSerializer(serializers.Serializer):
    """ Serializer for a file uploaded as a part of a response """
    downloadUrl = serializers.URLField(source='download_url')
    description = serializers.CharField()
    name = serializers.CharField()


class ResponseSerializer(serializers.Serializer):
    """ Serializer for the responseData api construct, which represents the contents of a submitted learner response """
    files = serializers.ListField(child=UploadedFileSerializer(), allow_empty=True)
    text = serializers.ListField(child=serializers.CharField(), allow_empty=True)


class AssessmentCriteriaSerializer(serializers.Serializer):
    """ Serializer for information about a criterion, in the context of a completed assessment """
    name = serializers.CharField()
    feedback = serializers.CharField()
    points = serializers.IntegerField()
    selectedOption = serializers.CharField(source='option')


class GradeDataSerializer(serializers.Serializer):
    """ Serializer for the `gradeData` api construct, which represents a completed staff assessment """
    score = ScoreField(required=False)
    overallFeedback = serializers.CharField(source='feedback', required=False)
    criteria = serializers.ListField(child=AssessmentCriteriaSerializer(), allow_empty=True, required=False)


class SubmissionDetailResponseSerializer(serializers.Serializer):
    """ Serializer for the response from the submission """
    gradeData = GradeDataSerializer(source='submission_and_assessment_info.assessment')
    response = ResponseSerializer(source='submission_and_assessment_info.submission')
    gradeStatus = serializers.SerializerMethodField()
    lockStatus = LockStatusField(source='lock_info.lock_status')

    def get_gradeStatus(self, obj):
        if obj.get('submission_and_assessment_info', {}).get('assessment'):
            return 'graded'
        else:
            return 'ungraded'


class LockStatusSerializer(serializers.Serializer):
    """
    Info about the status of a submission lock, with extra metadata stripped out.
    """
    lockStatus = LockStatusField(source='lock_status')

    class Meta:
        fields = [
            'lockStatus'
        ]
        read_only_fields = fields
