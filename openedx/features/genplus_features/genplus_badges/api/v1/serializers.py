"""
Serializers for Badges
"""


from rest_framework import serializers

from lms.djangoapps.badges.models import BadgeClass, BadgeAssertion
from openedx.features.genplus_features.genplus_badges.models import BoosterBadge, BoosterBadgeAward
from openedx.features.genplus_features.genplus_learning.models import Program


class UnitBadgeSerializer(serializers.ModelSerializer):
    image_url = serializers.ImageField(source='image')
    awarded = serializers.SerializerMethodField()
    awarded_on = serializers.SerializerMethodField()

    class Meta:
        model = BadgeClass
        fields = ('slug', 'display_name', 'course_id', 'image_url', 'awarded', 'awarded_on',)

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
        fields = ('slug', 'display_name', 'image_url', 'unit_badges', 'awarded', 'awarded_on',)

    def get_unit_badges(self, obj):
        program = Program.objects.filter(slug=obj.slug).first()
        unit_badges = BadgeClass.objects.none()
        if program:
            unit_ids = program.units.all().order_by('order').values_list('course', flat=True)
            unit_badges = BadgeClass.objects.prefetch_related('badgeassertion_set').filter(course_id__in=unit_ids,
                                                                                           issuing_component='genplus__unit')

        return UnitBadgeSerializer(unit_badges, many=True, read_only=True, context=self.context).data

    def get_awarded(self, obj):
        assertion = obj.get_for_user(self.context.get('user')).first()
        return True if assertion else False

    def get_awarded_on(self, obj):
        assertion = obj.get_for_user(self.context.get('user')).first()
        return assertion.created if assertion else None
