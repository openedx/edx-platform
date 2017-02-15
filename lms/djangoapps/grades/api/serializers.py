"""
API Serializers
"""
from collections import defaultdict
from rest_framework import serializers


# pylint: disable=abstract-method
class GradingPolicySerializer(serializers.Serializer):
    """
    Serializer for course grading policy.
    """
    assignment_type = serializers.CharField(source='type')
    count = serializers.IntegerField(source='min_count')
    dropped = serializers.IntegerField(source='drop_count')
    weight = serializers.FloatField()

    def to_representation(self, obj):
        """
        Return a representation of the grading policy.
        """
        # Backwards compatibility with the behavior of DRF v2.
        # When the grader dictionary was missing keys, DRF v2 would default to None;
        # DRF v3 unhelpfully raises an exception.
        return dict(
            super(GradingPolicySerializer, self).to_representation(
                defaultdict(lambda: None, obj)
            )
        )
