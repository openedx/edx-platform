"""
Progress Tab Serializers
"""
from rest_framework import serializers
from rest_framework.reverse import reverse
from lms.djangoapps.course_home_api.mixins import VerifiedModeSerializerMixin


class CourseGradeSerializer(serializers.Serializer):
    """
    Serializer for course grade
    """
    letter_grade = serializers.CharField()
    percent = serializers.FloatField()
    is_passing = serializers.BooleanField(source='passed')


class SubsectionScoresSerializer(serializers.Serializer):
    """
    Serializer for subsections in section_scores
    """
    assignment_type = serializers.CharField(source='format')
    display_name = serializers.CharField()
    block_key = serializers.SerializerMethodField()
    has_graded_assignment = serializers.BooleanField(source='graded')
    learner_has_access = serializers.SerializerMethodField()
    num_points_earned = serializers.FloatField(source='graded_total.earned')
    num_points_possible = serializers.FloatField(source='graded_total.possible')
    percent_graded = serializers.FloatField()
    show_correctness = serializers.CharField()
    show_grades = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()

    def get_block_key(self, subsection):
        return str(subsection.location)

    def get_url(self, subsection):
        relative_path = reverse('jump_to', args=[self.context['course_key'], subsection.location])
        request = self.context['request']
        return request.build_absolute_uri(relative_path)

    def get_show_grades(self, subsection):
        return subsection.show_grades(self.context['staff_access'])

    def get_learner_has_access(self, subsection):
        course_blocks = self.context['course_blocks']
        return not course_blocks.get_xblock_field(subsection.location, 'contains_gated_content', False)


class SectionScoresSerializer(serializers.Serializer):
    """
    Serializer for sections in section_scores
    """
    display_name = serializers.CharField()
    subsections = SubsectionScoresSerializer(source='sections', many=True)


class GradingPolicySerializer(serializers.Serializer):
    """
    Serializer for grading policy
    """
    assignment_policies = serializers.SerializerMethodField()
    grade_range = serializers.DictField(source='GRADE_CUTOFFS')

    def get_assignment_policies(self, grading_policy):
        return [{
            'num_droppable': assignment_policy['drop_count'],
            'num_total': assignment_policy['min_count'],
            'short_label': assignment_policy.get('short_label', ''),
            'type': assignment_policy['type'],
            'weight': assignment_policy['weight'],
        } for assignment_policy in grading_policy['GRADER']]


class CertificateDataSerializer(serializers.Serializer):
    """
    Serializer for certificate data
    """
    cert_status = serializers.CharField()
    cert_web_view_url = serializers.CharField()
    download_url = serializers.CharField()
    certificate_available_date = serializers.DateTimeField()


class VerificationDataSerializer(serializers.Serializer):
    """
    Serializer for verification data object
    """
    link = serializers.URLField()
    status = serializers.CharField()
    status_date = serializers.DateTimeField()


class ProgressTabSerializer(VerifiedModeSerializerMixin):
    """
    Serializer for progress tab
    """
    username = serializers.CharField()
    certificate_data = CertificateDataSerializer()
    completion_summary = serializers.DictField()
    course_grade = CourseGradeSerializer()
    end = serializers.DateTimeField()
    user_has_passing_grade = serializers.BooleanField()
    has_scheduled_content = serializers.BooleanField()
    section_scores = SectionScoresSerializer(many=True)
    enrollment_mode = serializers.CharField()
    grading_policy = GradingPolicySerializer()
    studio_url = serializers.CharField()
    verification_data = VerificationDataSerializer()
