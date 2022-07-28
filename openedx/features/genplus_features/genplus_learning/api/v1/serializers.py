from rest_framework import serializers

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.features.genplus_features.genplus_learning.models import (
    YearGroup,
    Program,
    ProgramEnrollment,
    ProgramUnitEnrollment,
    ClassUnit,
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
        gen_user = self.context.get("gen_user")
        is_locked = True
        if gen_user.is_student:
            gen_class = ProgramEnrollment.objects.get(
                student=gen_user.student,
                program=obj.program,
            ).gen_class
            is_locked = ClassUnit.objects.get(gen_class=gen_class, unit=obj).is_locked
        elif gen_user.is_teacher:
            is_locked = False

        return is_locked

    def get_progress(self, obj):
        gen_user = self.context.get("gen_user")
        if gen_user.is_student:
            return get_unit_progress(obj.course.id, gen_user.user)
        return None


class ProgramSerializer(serializers.ModelSerializer):
    units = UnitSerializer(many=True, read_only=True)
    year_group_name = serializers.CharField(source='year_group.name')
    program_name = serializers.CharField(source='year_group.program_name')

    class Meta:
        model = Program
        fields = ('program_name', 'year_group_name', 'units')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['units'].context.update(self.context)
