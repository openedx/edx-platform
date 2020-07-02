"""
Progress Tab Serializers
"""
from rest_framework import serializers
from lms.djangoapps.course_home_api.outline.v1.serializers import CourseBlockSerializer
from rest_framework.reverse import reverse


class GradedTotalSerializer(serializers.Serializer):
    earned = serializers.FloatField()
    first_attempted = serializers.CharField()
    graded = serializers.BooleanField()
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


class ProgressTabSerializer(serializers.Serializer):
    """
    Serializer for progress tab
    """
    course_blocks = CourseBlockSerializer()
    courseware_summary = ChapterSerializer(many=True)
    enrollment_mode = serializers.CharField()
    user_timezone = serializers.CharField()
