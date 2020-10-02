"""
Progress Tab Serializers
"""
from rest_framework import serializers
from rest_framework.reverse import reverse
from lms.djangoapps.certificates.models import CertificateStatuses


class GradedTotalSerializer(serializers.Serializer):
    earned = serializers.FloatField()
    possible = serializers.FloatField()


class SubsectionSerializer(serializers.Serializer):
    display_name = serializers.CharField()
    due = serializers.DateTimeField()
    format = serializers.CharField()
    graded = serializers.BooleanField()
    graded_total = GradedTotalSerializer()
    # TODO: override serializer
    percent_graded = serializers.FloatField()
    problem_scores = serializers.SerializerMethodField()
    show_correctness = serializers.CharField()
    show_grades = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()

    def get_url(self, subsection):
        relative_path = reverse('jump_to', args=[self.context['course_key'], subsection.location])
        request = self.context['request']
        return request.build_absolute_uri(relative_path)

    def get_problem_scores(self, subsection):
        problem_scores = [
            {
                'earned': score.earned,
                'possible': score.possible,
            }
            for score in subsection.problem_scores.values()
        ]
        return problem_scores

    def get_show_grades(self, subsection):
        return subsection.show_grades(self.context['staff_access'])


class ChapterSerializer(serializers.Serializer):
    """
    Serializer for chapters in coursewaresummary
    """
    display_name = serializers.CharField()
    subsections = SubsectionSerializer(source='sections', many=True)


class CertificateDataSerializer(serializers.Serializer):
    cert_status = serializers.CharField()
    cert_web_view_url = serializers.CharField()
    download_url = serializers.CharField()
    msg = serializers.CharField()
    title = serializers.CharField()


class CreditRequirementSerializer(serializers.Serializer):
    """
    Serializer for credit requirement objects
    """
    display_name = serializers.CharField()
    min_grade = serializers.SerializerMethodField()
    status = serializers.CharField()
    status_date = serializers.DateTimeField()

    def get_min_grade(self, requirement):
        if requirement['namespace'] == 'grade':
            return requirement['criteria']['min_grade'] * 100
        else:
            return None


class CreditCourseRequirementsSerializer(serializers.Serializer):
    """
    Serializer for credit_course_requirements
    """
    dashboard_url = serializers.SerializerMethodField()
    eligibility_status = serializers.CharField()
    requirements = CreditRequirementSerializer(many=True)

    def get_dashboard_url(self, _):
        relative_path = reverse('dashboard')
        request = self.context['request']
        return request.build_absolute_uri(relative_path)


class VerificationDataSerializer(serializers.Serializer):
    """
    Serializer for verification data object
    """
    link = serializers.URLField()
    status = serializers.CharField()
    status_date = serializers.DateTimeField()


class ProgressTabSerializer(serializers.Serializer):
    """
    Serializer for progress tab
    """
    certificate_data = CertificateDataSerializer()
    credit_course_requirements = CreditCourseRequirementsSerializer()
    credit_support_url = serializers.URLField()
    courseware_summary = ChapterSerializer(many=True)
    enrollment_mode = serializers.CharField()
    studio_url = serializers.CharField()
    user_timezone = serializers.CharField()
    verification_data = VerificationDataSerializer()
