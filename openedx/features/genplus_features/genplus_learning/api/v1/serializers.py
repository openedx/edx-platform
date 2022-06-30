from rest_framework import serializers

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.features.genplus_features.genplus_learning.models import (
    YearGroup,
    Program,
    ProgramEnrollment,
    ProgramUnitEnrollment,
)
from openedx.features.genplus_features.genplus_learning.utils import get_lms_link_for_unit, is_unit_locked, get_user_unit_progress
from openedx.features.genplus_features.genplus_learning.constants import ProgramEnrollmentStatuses


class UnitSerializer(serializers.ModelSerializer):
    is_locked = serializers.SerializerMethodField()
    lms_url = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()

    class Meta:
        model = CourseOverview
        fields = ('id', 'display_name', 'short_description',
                'course_image_url', 'is_locked', 'lms_url',
                'progress')

    def get_is_locked(self, obj):
        return is_unit_locked(obj.id)

    def get_lms_url(self, obj):
        return get_lms_link_for_unit(obj.id)

    def get_progress(self, obj):
        gen_user = self.context.get("gen_user")
        if gen_user.is_student:
            return get_user_unit_progress(obj, gen_user.user)
        return None


class YearGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = YearGroup
        fields = ('name', 'program_name')


class LessonSerializer(serializers.ModelSerializer):
    units = serializers.SerializerMethodField()
    year_group_name = serializers.CharField(source='year_group.name')
    program_name = serializers.CharField(source='year_group.program_name')

    class Meta:
        model = YearGroup
        fields = ('program_name', 'year_group_name', 'units')

    def get_units(self, obj):
        gen_user = self.context.get("gen_user")
        units = obj.units.all()
        if gen_user.is_student:
            program_enrollment = ProgramEnrollment.objects.get(
                gen_user=gen_user,
                program=obj,
                status=ProgramEnrollmentStatuses.ENROLLED
            )
            student_unit_ids = ProgramUnitEnrollment.objects.filter(
                program_enrollment=program_enrollment
            ).values_list('unit', flat=True)
            units = units.filter(id__in=student_unit_ids)

        return UnitSerializer(units, many=True, read_only=True, context = {'gen_user': gen_user}).data
