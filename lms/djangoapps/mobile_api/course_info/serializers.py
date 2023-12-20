"""
Course Info serializers
"""
from rest_framework import serializers

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview


class CourseInfoOverviewSerializer(serializers.ModelSerializer):
    """
    Serializer for serialize additional fields in BlocksInfoInCourseView.
    """

    name = serializers.CharField(source='display_name')
    number = serializers.CharField(source='display_number_with_default')
    org = serializers.CharField(source='display_org_with_default')
    is_self_paced = serializers.BooleanField(source='self_paced')
    media = serializers.SerializerMethodField()

    class Meta:
        model = CourseOverview
        fields = (
            'name',
            'number',
            'org',
            'start',
            'start_display',
            'start_type',
            'end',
            'is_self_paced',
            'media',
        )

    @staticmethod
    def get_media(obj):
        return {'image': obj.image_urls}
