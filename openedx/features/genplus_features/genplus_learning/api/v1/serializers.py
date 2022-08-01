from rest_framework import serializers

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.features.genplus_features.genplus_learning.models import (
    Program,
    ProgramEnrollment,
    Unit,
)
from openedx.features.genplus_features.genplus_learning.utils import (
    get_unit_progress,
)
from openedx.features.genplus_features.genplus_learning.constants import ProgramEnrollmentStatuses


class UnitSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    is_locked = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()

    class Meta:
        model = Unit
        fields = ('id', 'display_name', 'short_description',
                'banner_image_url', 'is_locked', 'lms_url',
                'progress')

    def get_id(self, obj):
        return str(obj.course.id)

    def get_is_locked(self, obj):
        units_context = self.context.get("units_context")
        return units_context[obj.pk]['is_locked']

    def get_progress(self, obj):
        units_context = self.context.get("units_context")
        return units_context[obj.pk]['progress']


class ProgramSerializer(serializers.ModelSerializer):
    units = serializers.SerializerMethodField()
    year_group_name = serializers.CharField(source='year_group.name')
    program_name = serializers.CharField(source='year_group.program_name')

    class Meta:
        model = Program
        fields = ('program_name', 'year_group_name', 'units')

    def get_units(self, obj):
        gen_user = self.context.get('gen_user')
        units = obj.units.all()
        units_context = {}

        for unit in units:
            units_context[unit.pk] = {}
            if gen_user.is_student:
                enrollment = gen_user.student.program_enrollments.get(program=obj)
                units_context[unit.pk] = {
                    'is_locked': unit.is_locked(enrollment.gen_class),
                    'progress': get_unit_progress(unit.course.id, gen_user.user),
                }
            else:
                units_context[unit.pk] = {
                    'is_locked': False,
                    'progress': None,
                }

        return UnitSerializer(units, many=True, read_only=True, context={'units_context': units_context}).data
