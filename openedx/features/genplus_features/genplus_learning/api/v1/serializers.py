from rest_framework import serializers

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.features.genplus_features.genplus_learning.models import YearGroup, Program
from openedx.features.genplus_features.genplus_learning.utils import get_lms_link_for_unit, is_unit_locked


class UnitSerializer(serializers.ModelSerializer):
    is_locked = serializers.SerializerMethodField()
    lms_url = serializers.SerializerMethodField()

    def get_is_locked(self, obj):
        return is_unit_locked(obj.id)

    def get_lms_url(self, obj):
        return get_lms_link_for_unit(obj.id)

    class Meta:
        model = CourseOverview
        fields = ('id', 'display_name', 'short_description',
                'course_image_url', 'is_locked', 'lms_url')


class YearGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = YearGroup
        fields = ('name', 'program_name')


class LessonSerializer(serializers.ModelSerializer):
    units = UnitSerializer(read_only=True, many=True)
    year_group_name = serializers.CharField(source='year_group.name')
    program_name = serializers.CharField(source='year_group.program_name')

    class Meta:
        model = YearGroup
        fields = ('program_name', 'year_group_name', 'units')
