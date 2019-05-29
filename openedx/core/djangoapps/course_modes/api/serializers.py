"""
Course modes API serializers.
"""
from __future__ import absolute_import

from rest_framework import serializers

from openedx.core.djangoapps.course_modes.models import CourseMode


class CourseModeSerializer(serializers.Serializer):
    """
    Serializer for the CourseMode model.
    The ``course_id``, ``mode_slug``, ``mode_display_name``, and ``currency`` fields
    are all required for a create operation.  Neither the ``course_id``
    nor the ``mode_slug`` fields can be modified during an update operation.
    """
    UNCHANGEABLE_FIELDS = {'course_id', 'mode_slug'}

    course_id = serializers.CharField()
    mode_slug = serializers.CharField()
    mode_display_name = serializers.CharField()
    min_price = serializers.IntegerField(required=False)
    currency = serializers.CharField()
    expiration_datetime = serializers.DateTimeField(required=False)
    expiration_datetime_is_explicit = serializers.BooleanField(required=False)
    description = serializers.CharField(required=False)
    sku = serializers.CharField(required=False)
    bulk_sku = serializers.CharField(required=False)

    def create(self, validated_data):
        """
        This method must be implemented for use in our
        ListCreateAPIView.
        """
        return CourseMode.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """
        This method must be implemented for use in our
        RetrieveUpdateDestroyAPIView.
        """
        errors = {}

        for field in validated_data:
            if field in self.UNCHANGEABLE_FIELDS:
                errors[field] = ['This field cannot be modified.']

        if errors:
            raise serializers.ValidationError(errors)

        for modifiable_field in validated_data:
            setattr(
                instance,
                modifiable_field,
                validated_data.get(modifiable_field, getattr(instance, modifiable_field))
            )
        instance.save()
        return instance
