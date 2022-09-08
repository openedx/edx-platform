"""
Serializers for Badges
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from lms.djangoapps.badges.models import BadgeClass, BadgeAssertion
from openedx.features.genplus_features.genplus_badges.models import BoosterBadge, BoosterBadgeAward
from openedx.features.genplus_features.genplus_learning.models import Program
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

    class Meta:
        model = BadgeClass
        fields = (
            'slug',
            'display_name',
            'image_url',
            'unit_badges',
            'awarded',
            'awarded_on',
        )

    def get_unit_badges(self, obj):
        program = Program.objects.filter(slug=obj.slug).first()
        unit_badges = BadgeClass.objects.none()
        if program:
            unit_ids = program.units.all().order_by('order').values_list(
                'course', flat=True)
            unit_badges = BadgeClass.objects.prefetch_related(
                'badgeassertion_set').filter(course_id__in=unit_ids,
                                             issuing_component='genplus__unit')

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


class AwardBoosterBadgesSerializer(serializers.ModelSerializer):
    user = serializers.ListField(child=serializers.CharField())
    badge = serializers.ListField(child=serializers.CharField())
    feedback = serializers.CharField()

    class Meta:
        model = BoosterBadgeAward
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

        return BoosterBadgeAward.objects.bulk_create(awards,
                                                     ignore_conflicts=True)

    def validate_user(self, value):
        if not value or len(value) < 1:
            raise serializers.ValidationError('This field may not be blank.')
        return value

    def validate_badge(self, value):
        if not value or len(value) < 1:
            raise serializers.ValidationError('This field may not be blank.')
        return value


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
