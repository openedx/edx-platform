"""
Serializers for Badges
"""
from rest_framework import serializers

from badges.models import BadgeClass, BadgeAssertion


class BadgeClassSerializer(serializers.ModelSerializer):
    """
    Serializer for BadgeClass model.
    """
    image_url = serializers.ImageField(source='image')

    class Meta(object):
        model = BadgeClass
        fields = ('slug', 'issuing_component', 'display_name', 'course_id', 'description', 'criteria', 'image_url')


class BadgeAssertionSerializer(serializers.ModelSerializer):
    """
    Serializer for the BadgeAssertion model.
    """
    badge_class = BadgeClassSerializer(read_only=True)

    class Meta(object):
        model = BadgeAssertion
        fields = ('badge_class', 'image_url', 'assertion_url', 'created')
