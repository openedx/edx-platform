from django.conf import settings
from rest_framework import serializers
from xmodule.modulestore.django import modulestore
from common.djangoapps.student.models import CourseEnrollment
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.features.genplus_features.genplus_learning.models import (
    Program,
    ProgramEnrollment,
    Unit,
    ClassLesson,
    ClassUnit,
    UnitCompletion,
    UnitBlockCompletion,
)
from openedx.features.genplus_features.genplus_learning.utils import (
    calculate_class_lesson_progress,
    get_absolute_url,
)
from openedx.features.genplus_features.genplus.models import Student, JournalPost, Activity, Teacher
from openedx.features.genplus_features.genplus_badges.models import BoosterBadgeAward
from openedx.features.genplus_features.genplus.api.v1.serializers import TeacherSerializer
from openedx.features.genplus_features.common.utils import get_generic_serializer


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


class AssessmentUnitSerializer(serializers.ModelSerializer):
    is_locked = serializers.SerializerMethodField()
    lms_url = serializers.SerializerMethodField()
    is_complete = serializers.SerializerMethodField()

    class Meta:
        model = CourseOverview
        fields = ('id', 'display_name', 'short_description',
                  'course_image_url', 'is_locked', 'lms_url',
                  'is_complete')

    def get_is_locked(self, obj):
        return self.context.get('is_locked', False)

    def get_is_complete(self, obj):
        return self.context.get('is_complete', False)

    def get_lms_url(self, obj):
        course = modulestore().get_course(obj.id)
        course_key_str = str(obj.id)
        sections = course.children
        if sections:
            usage_key_str = str(sections[0])
        else:
            usage_key_str = str(modulestore().make_course_usage_key(course.id))

        return f"{settings.LMS_ROOT_URL}/courses/{course_key_str}/jump_to/{usage_key_str}"


class ProgramSerializer(serializers.ModelSerializer):
    units = serializers.SerializerMethodField()
    intro_unit = serializers.SerializerMethodField()
    outro_unit = serializers.SerializerMethodField()
    year_group_name = serializers.CharField(source='year_group.name')
    program_name = serializers.CharField(source='year_group.program_name')

    class Meta:
        model = Program
        fields = ('program_name', 'year_group_name', 'intro_unit', 'units', 'outro_unit')

    def get_units(self, obj):
        gen_user = self.context.get('gen_user')
        units = obj.units.all()
        completions = UnitCompletion.objects.filter(
            user=gen_user.user,
            course_key__in=units.values_list('course', flat=True)
        )
        units_context = {}

        for unit in units:
            is_locked = False
            progress = None

            if gen_user.is_student:
                enrollment = gen_user.student.program_enrollments.get(program=obj)
                completion = completions.filter(user=gen_user.user, course_key=unit.course.id).first()
                progress = completion.progress if completion else 0
                if CourseEnrollment.is_enrolled(gen_user.user, unit.course.id):
                    is_locked = unit.is_locked(enrollment.gen_class)
                else:
                    is_locked = True

            units_context[unit.pk] = {
                'is_locked': is_locked,
                'progress': progress,
            }

        return UnitSerializer(units, many=True, read_only=True, context={'units_context': units_context}).data

    def get_intro_unit(self, obj):
        if not obj.intro_unit:
            return None

        gen_user = self.context.get('gen_user')
        context = {
            'is_locked': False,
            'is_complete': False,
        }
        if gen_user.is_student:
            completion = UnitCompletion.objects.filter(user=gen_user.user, course_key=obj.intro_unit.id).first()
            context['is_complete'] = completion.is_complete if completion else False

        return AssessmentUnitSerializer(obj.intro_unit, read_only=True, context=context).data

    def get_outro_unit(self, obj):
        if not obj.outro_unit:
            return None

        gen_user = self.context.get('gen_user')
        context = {
            'is_locked': False,
            'is_complete': False,
        }
        if gen_user.is_student:
            completion = UnitCompletion.objects.filter(user=gen_user.user, course_key=obj.outro_unit.id).first()
            context['is_complete'] = completion.is_complete if completion else False

        return AssessmentUnitSerializer(obj.outro_unit, read_only=True, context=context).data


class ClassLessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassLesson
        fields = ('id', 'order', 'display_name', 'is_locked', 'lms_url')


class ClassUnitSerializer(serializers.ModelSerializer):
    class_lessons = serializers.SerializerMethodField()
    display_name = serializers.CharField(source="unit.display_name")

    class Meta:
        model = ClassUnit
        fields = ('id', 'display_name', 'is_locked', 'class_lessons',)

    def get_class_lessons(self, obj):
        queryset = obj.class_lessons.all().order_by('order')
        serializer = ClassLessonSerializer(queryset, many=True, read_only=True)
        return serializer.data


class ClassStudentSerializer(serializers.ModelSerializer):
    user_id = serializers.CharField(source='gen_user.user.id', default=None)
    username = serializers.SerializerMethodField()
    profile_pic = serializers.SerializerMethodField()
    skills_assessment = serializers.SerializerMethodField()
    unit_lesson_completion = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = ('id', 'user_id', 'username', 'profile_pic', 'skills_assessment', 'unit_lesson_completion')

    def get_username(self, obj):
        edx_user = obj.gen_user.user
        return edx_user.get_full_name() if edx_user else obj.gen_user.email

    def get_profile_pic(self, obj):
        profile = obj.character.profile_pic if obj.character else None
        request = self.context.get('request')
        return get_absolute_url(request, profile)

    def get_skills_assessment(self, obj):
        return True

    def get_unit_lesson_completion(self, obj):
        results = []
        class_units = self.context.get('class_units')
        for class_unit in class_units:
            progress = {'unit_display_name': class_unit.unit.display_name}
            chapters = modulestore().get_course(class_unit.course_key).children
            completion_qs = UnitBlockCompletion.objects.filter(user=obj.user,
                                                               usage_key__in=chapters,
                                                               block_type='chapter',
                                                               is_complete=True)
            completions = completion_qs.values_list('usage_key', flat=True)
            for index, key in enumerate(chapters):
                chapters[index] = True if key in completions else False
            progress['lesson_completions'] = chapters
            results.append(progress)
        return results


StudentSerializer = get_generic_serializer({'name': Student, 'fields': '__all__'})
JournalPostSerializer = get_generic_serializer({'name': JournalPost, 'fields': '__all__'})
UnitBlockCompletionSerializer = get_generic_serializer({'name': UnitBlockCompletion,
                                                        'fields': ('usage_key',
                                                                   'course_name',
                                                                   'lesson_name')})
BoosterBadgeAwardSerializer = get_generic_serializer({'name': BoosterBadgeAward, 'fields': '__all__'})


class ContentObjectRelatedField(serializers.RelatedField):

    def to_representation(self, value):
        if isinstance(value, Student):
            serializer = StudentSerializer(value)
        elif isinstance(value, Teacher):
            serializer = TeacherSerializer(value)
        elif isinstance(value, UnitBlockCompletion):
            serializer = UnitBlockCompletionSerializer(value)
        elif isinstance(value, BoosterBadgeAward):
            serializer = BoosterBadgeAwardSerializer(value)
        elif isinstance(value, JournalPost):
            serializer = JournalPostSerializer(value)
        else:
            raise Exception('Unexpected type of tagged object')

        return serializer.data


class ActivitySerializer(serializers.ModelSerializer):
    actor = ContentObjectRelatedField(read_only=True)
    action_object = ContentObjectRelatedField(read_only=True)
    target = ContentObjectRelatedField(read_only=True)

    class Meta:
        model = Activity
        fields = ('id', 'type', 'actor', 'action_object', 'target', 'is_read', 'created')
