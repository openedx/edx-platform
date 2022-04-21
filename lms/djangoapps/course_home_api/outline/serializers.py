"""
Outline Tab Serializers.
"""

from django.utils.translation import ngettext
from rest_framework import serializers

from lms.djangoapps.course_home_api.dates.serializers import DateSummarySerializer
from lms.djangoapps.course_home_api.progress.serializers import CertificateDataSerializer
from lms.djangoapps.course_home_api.serializers import DatesBannerSerializer, VerifiedModeSerializer


class CourseBlockSerializer(serializers.Serializer):
    """
    Serializer for Course Block Objects
    """
    blocks = serializers.SerializerMethodField()

    def get_blocks(self, block):  # pylint: disable=missing-function-docstring
        block_key = block['id']
        block_type = block['type']
        children = block.get('children', []) if block_type != 'sequential' else []  # Don't descend past sequential
        description = block.get('format')
        display_name = block['display_name']
        enable_links = self.context.get('enable_links')
        graded = block.get('graded')
        icon = None
        num_graded_problems = block.get('num_graded_problems', 0)
        scored = block.get('scored')

        if num_graded_problems and block_type == 'sequential':
            questions = ngettext('({number} Question)', '({number} Questions)', num_graded_problems)
            display_name += ' ' + questions.format(number=num_graded_problems)

        if graded and scored:
            icon = 'fa-pencil-square-o'

        if 'special_exam_info' in block:
            description = block['special_exam_info'].get('short_description')
            icon = block['special_exam_info'].get('suggested_icon', 'fa-pencil-square-o')

        serialized = {
            block_key: {
                'children': [child['id'] for child in children],
                'complete': block.get('complete', False),
                'description': description,
                'display_name': display_name,
                'due': block.get('due'),
                'effort_activities': block.get('effort_activities'),
                'effort_time': block.get('effort_time'),
                'icon': icon,
                'id': block_key,
                'lms_web_url': block['lms_web_url'] if enable_links else None,
                'resume_block': block.get('resume_block', False),
                'type': block_type,
                'has_scheduled_content': block.get('has_scheduled_content'),
            },
        }
        for child in children:
            serialized.update(self.get_blocks(child))
        return serialized


class CourseGoalsSerializer(serializers.Serializer):
    """
    Serializer for Course Goal data
    """
    selected_goal = serializers.DictField()
    weekly_learning_goal_enabled = serializers.BooleanField(default=False)


class CourseToolSerializer(serializers.Serializer):
    """
    Serializer for Course Tool Objects
    """
    analytics_id = serializers.CharField()
    title = serializers.CharField()
    url = serializers.SerializerMethodField()

    def get_url(self, tool):
        course_overview = self.context.get('course_overview')
        url = tool.url(course_overview.id)
        request = self.context.get('request')
        return request.build_absolute_uri(url)


class DatesWidgetSerializer(serializers.Serializer):
    """
    Serializer for Dates Widget data
    """
    course_date_blocks = DateSummarySerializer(many=True)
    dates_tab_link = serializers.CharField()
    user_timezone = serializers.CharField()


class EnrollAlertSerializer(serializers.Serializer):
    """
    Serializer for enroll alert information
    """
    can_enroll = serializers.BooleanField()
    extra_text = serializers.CharField()


class ResumeCourseSerializer(serializers.Serializer):
    """
    Serializer for resume course data
    """
    has_visited_course = serializers.BooleanField()
    url = serializers.URLField()


class OutlineTabSerializer(DatesBannerSerializer, VerifiedModeSerializer):
    """
    Serializer for the Outline Tab
    """
    access_expiration = serializers.DictField()
    cert_data = CertificateDataSerializer()
    course_blocks = CourseBlockSerializer()
    course_goals = CourseGoalsSerializer()
    course_tools = CourseToolSerializer(many=True)
    dates_widget = DatesWidgetSerializer()
    enroll_alert = EnrollAlertSerializer()
    enrollment_mode = serializers.CharField()
    enable_proctored_exams = serializers.BooleanField()
    handouts_html = serializers.CharField()
    has_ended = serializers.BooleanField()
    offer = serializers.DictField()
    resume_course = ResumeCourseSerializer()
    welcome_message_html = serializers.CharField()
    user_has_passing_grade = serializers.BooleanField()
