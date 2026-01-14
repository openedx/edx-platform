"""Serializer for Instructor Dashboard API v2."""
from rest_framework import serializers


class ORASerializer(serializers.Serializer):
    """Serializer for Open Response Assessments (ORAs) in a course."""

    block_id = serializers.CharField(source="id")
    unit_name = serializers.CharField(source="parent_name")
    display_name = serializers.CharField(source="name")

    # Metrics fields
    total_responses = serializers.IntegerField(source="total")
    training = serializers.IntegerField()
    peer = serializers.IntegerField()
    self = serializers.IntegerField()
    waiting = serializers.IntegerField()
    staff = serializers.IntegerField()
    final_grade_received = serializers.IntegerField()
