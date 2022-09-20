"""
Serializers for Badges
"""
from django.conf import settings
from rest_framework import serializers
from django.contrib.auth.models import User
from lms.djangoapps.badges.models import BadgeClass, BadgeAssertion
from openedx.features.genplus_features.genplus_badges.models import BoosterBadge, BoosterBadgeAward
from openedx.features.genplus_features.genplus_learning.models import Program
from openedx.features.genplus_features.genplus.models import Student, Teacher, JournalPost
from openedx.features.genplus_features.genplus.constants import JournalTypes
from openedx.features.genplus_features.genplus_badges.utils import get_absolute_url


class UnitBadgeSerializer(serializers.ModelSerializer):
    image_url = serializers.ImageField(source='image')
    awarded = serializers.SerializerMethodField()
    awarded_on = serializers.SerializerMethodField()

    class Meta:
        model = BadgeClass
        fields = (
            'slug',
            'display_name',
            'course_id',
            'image_url',
            'awarded',
            'awarded_on',
        )

    def get_awarded(self, obj):
        assertion = obj.get_for_user(self.context.get('user')).first()
        return True if assertion else False

    def get_awarded_on(self, obj):
        assertion = obj.get_for_user(self.context.get('user')).first()
        return assertion.created if assertion else None


class ProgramBadgeSerializer(serializers.ModelSerializer):
    image_url = serializers.ImageField(source='image')
    unit_badges = serializers.SerializerMethodField()
    awarded = serializers.SerializerMethodField()
    awarded_on = serializers.SerializerMethodField()
    banner_image_url = serializers.SerializerMethodField()

    class Meta:
        model = BadgeClass
        fields = (
            'slug',
            'display_name',
            'image_url',
            'unit_badges',
            'awarded',
            'awarded_on',
            'banner_image_url',
        )

    def get_unit_badges(self, obj):
        program = Program.objects.filter(slug=obj.slug).first()
        unit_badges = BadgeClass.objects.none()
        if program:
            units = program.units.all().values(
                'course', 'order')
            unit_ids = units.values_list('course', flat=True)
            unit_order = {unit['course']: unit['order'] for unit in units}
            unit_badges = BadgeClass.objects.prefetch_related(
                'badgeassertion_set').filter(course_id__in=unit_ids,
                                             issuing_component='genplus__unit')

            unit_badges = sorted(unit_badges, key=lambda unit: unit_order[unit.course_id])

        return UnitBadgeSerializer(unit_badges,
                                   many=True,
                                   read_only=True,
                                   context=self.context).data

    def get_awarded(self, obj):
        assertion = obj.get_for_user(self.context.get('user')).first()
        return True if assertion else False

    def get_awarded_on(self, obj):
        assertion = obj.get_for_user(self.context.get('user')).first()
        return assertion.created if assertion else None

    def get_banner_image_url(self, obj):
        program = Program.objects.filter(slug=obj.slug).first()
        return f"{settings.LMS_ROOT_URL}{program.banner_image.url}" if program.banner_image else ''


class AwardBoosterBadgesSerializer(serializers.Serializer):
    user = serializers.ListField(child=serializers.CharField())
    badge = serializers.ListField(child=serializers.CharField())
    feedback = serializers.CharField(allow_blank=True)

    class Meta:
        fields = ('user', 'badge', 'feedback')

    def create(self, validated_data):
        users = validated_data.pop('user')
        badges = validated_data.pop('badge')
        feedback = validated_data.pop('feedback')
        request = self.context.get('request')

        user_qs = User.objects.filter(username__in=users)
        badge_qs = BoosterBadge.objects.filter(pk__in=badges)
        awards = []

        for user in user_qs:
            for badge in badge_qs:
                award = BoosterBadgeAward(user=user,
                                          badge=badge,
                                          awarded_by=request.user,
                                          feedback=feedback,
                                          image_url=get_absolute_url(
                                              request, badge.image))
                awards.append(award)

        if feedback and users:
            students = Student.objects.filter(gen_user__user__username__in=users)
            teacher = Teacher.objects.get(gen_user__user=request.user)
            journal_posts = [JournalPost(student=student, teacher=teacher,
                                         type=JournalTypes.TEACHER_FEEDBACK,
                                         description=feedback)
                             for student in students]
            JournalPost.objects.bulk_create(journal_posts)

        return BoosterBadgeAward.objects.bulk_create(awards,
                                                     ignore_conflicts=True)

    def validate(self, data):
        feedback = data['feedback']
        users = data['user']
        badges = data['badge']

        if not users:
            raise serializers.ValidationError('Provide students to give feedback or award badges to.')

        if users and not (feedback or badges):
            raise serializers.ValidationError('Give feedback or award badges to provided students.')

        return data


class BoosterBadgeSerializer(serializers.ModelSerializer):
    skill_name = serializers.CharField(source='skill.name')
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = BoosterBadge
        fields = ('id', 'slug', 'skill_name', 'display_name', 'image_url')

    def get_image_url(self, obj):
        request = self.context.get('request')
        return get_absolute_url(request, obj.image)


class ClassBoosterBadgesSerializer(serializers.ModelSerializer):
    class Meta:
        model = BoosterBadgeAward
        fields = ('user', 'badge', 'awarded_by', 'feedback', 'image_url')
