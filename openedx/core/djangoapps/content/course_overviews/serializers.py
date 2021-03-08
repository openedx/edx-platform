"""
CourseOverview serializers
"""
from rest_framework import serializers

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview


class CourseOverviewBaseSerializer(serializers.ModelSerializer):
    """
    Serializer for a course run overview.
    """

    class Meta:
        model = CourseOverview
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['display_name_with_default'] = instance.display_name_with_default
        representation['has_started'] = instance.has_started()
        representation['has_ended'] = instance.has_ended()
        representation['pacing'] = instance.pacing
        return representation
