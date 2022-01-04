"""
Progress Tab Serializers
"""
from datetime import datetime

from rest_framework import serializers
from rest_framework.reverse import reverse
from pytz import UTC

from lms.djangoapps.course_home_api.serializers import ReadOnlySerializer, VerifiedModeSerializer


class CourseGradeSerializer(ReadOnlySerializer):
    """
    Serializer for course grade
    """
    letter_grade = serializers.CharField()
    percent = serializers.FloatField()
    is_passing = serializers.BooleanField(source='passed')


class SubsectionScoresSerializer(ReadOnlySerializer):
    """
    Serializer for subsections in section_scores
    """
    assignment_type = serializers.CharField(source='format')
    block_key = serializers.SerializerMethodField()
    display_name = serializers.CharField()
    has_graded_assignment = serializers.BooleanField(source='graded')
    override = serializers.SerializerMethodField()
    learner_has_access = serializers.SerializerMethodField()
    num_points_earned = serializers.FloatField(source='graded_total.earned')
    num_points_possible = serializers.FloatField(source='graded_total.possible')
    percent_graded = serializers.FloatField()
    problem_scores = serializers.SerializerMethodField()
    show_correctness = serializers.CharField()
    show_grades = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()

    def get_override(self, subsection):
        """Proctoring or grading score override"""
        if subsection.override is None:
            return None
        else:
            return {
                "system": subsection.override.system,
                "reason": subsection.override.override_reason,
            }

    def get_block_key(self, subsection):
        return str(subsection.location)

    def get_problem_scores(self, subsection):
        """Problem scores for this subsection"""
        problem_scores = [
            {
                'earned': score.earned,
                'possible': score.possible,
            }
            for score in subsection.problem_scores.values()
        ]
        return problem_scores

    def get_url(self, subsection):
        """
        Returns the URL for the subsection while taking into account if the course team has
        marked the subsection's visibility as hide after due.
        """
        hide_url_date = subsection.end if subsection.self_paced else subsection.due
        if (not self.context['staff_access'] and subsection.hide_after_due and hide_url_date
                and datetime.now(UTC) > hide_url_date):
            return None

        relative_path = reverse('jump_to', args=[self.context['course_key'], subsection.location])
        request = self.context['request']
        return request.build_absolute_uri(relative_path)

    def get_show_grades(self, subsection):
        return subsection.show_grades(self.context['staff_access'])

    def get_learner_has_access(self, subsection):
        course_blocks = self.context['course_blocks']
        return not course_blocks.get_xblock_field(subsection.location, 'contains_gated_content', False)


class SectionScoresSerializer(ReadOnlySerializer):
    """
    Serializer for sections in section_scores
    """
    display_name = serializers.CharField()
    subsections = SubsectionScoresSerializer(source='sections', many=True)


class GradingPolicySerializer(ReadOnlySerializer):
    """
    Serializer for grading policy
    """
    assignment_policies = serializers.SerializerMethodField()
    grade_range = serializers.DictField(source='GRADE_CUTOFFS')

    def get_assignment_policies(self, grading_policy):
        return [{
            'num_droppable': assignment_policy['drop_count'],
            'num_total': float(assignment_policy['min_count']),
            'short_label': assignment_policy.get('short_label', ''),
            'type': assignment_policy['type'],
            'weight': assignment_policy['weight'],
        } for assignment_policy in grading_policy['GRADER']]


class CertificateDataSerializer(ReadOnlySerializer):
    """
    Serializer for certificate data
    """
    cert_status = serializers.CharField()
    cert_web_view_url = serializers.CharField()
    download_url = serializers.CharField()
    certificate_available_date = serializers.DateTimeField()


class VerificationDataSerializer(ReadOnlySerializer):
    """
    Serializer for verification data object
    """
    link = serializers.URLField()
    status = serializers.CharField()
    status_date = serializers.DateTimeField()


class ProgressTabSerializer(VerifiedModeSerializer):
    """
    Serializer for progress tab
    """
    access_expiration = serializers.DictField()
    certificate_data = CertificateDataSerializer()
    completion_summary = serializers.DictField()
    course_grade = CourseGradeSerializer()
    credit_course_requirements = serializers.DictField()
    end = serializers.DateTimeField()
    enrollment_mode = serializers.CharField()
    grading_policy = GradingPolicySerializer()
    has_scheduled_content = serializers.BooleanField()
    section_scores = SectionScoresSerializer(many=True)
    studio_url = serializers.CharField()
    username = serializers.CharField()
    user_has_passing_grade = serializers.BooleanField()
    verification_data = VerificationDataSerializer()
