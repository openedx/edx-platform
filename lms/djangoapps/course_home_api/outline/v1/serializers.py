"""
Outline Tab Serializers.
"""


from rest_framework import serializers


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


class OutlineTabSerializer(serializers.Serializer):
    """
    Serializer for the Outline Tab
    """
    course_tools = CourseToolSerializer(many=True)
