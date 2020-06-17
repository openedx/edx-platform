"""
Outline Tab Serializers.
"""

from rest_framework import serializers
from rest_framework.reverse import reverse


class CourseToolSerializer(serializers.Serializer):
    """
    Serializer for Course Tool Objects
    """
    analytics_id = serializers.CharField()
    title = serializers.CharField()
    url = serializers.SerializerMethodField()

    def get_url(self, tool):
        course_key = self.context.get('course_key')
        url = tool.url(course_key)
        request = self.context.get('request')
        return request.build_absolute_uri(url)


class CourseBlockSerializer(serializers.Serializer):
    """
    Serializer for Course Block Objects
    """
    blocks = serializers.SerializerMethodField()

    def get_blocks(self, blocks):
        return {
            str(block_key): {
                'id': str(block_key),
                'type': block_key.category,
                'display_name': blocks.get_xblock_field(block_key, 'display_name', block_key.category),
                'lms_web_url': reverse(
                    'jump_to',
                    kwargs={'course_id': str(block_key.course_key), 'location': str(block_key)},
                    request=self.context['request'],
                ),
                'children': [str(child_key) for child_key in blocks.get_children(block_key)],
            }
            for block_key in blocks
        }


class OutlineTabSerializer(serializers.Serializer):
    """
    Serializer for the Outline Tab
    """
    course_tools = CourseToolSerializer(many=True)
    course_blocks = CourseBlockSerializer()
