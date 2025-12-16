"""
Serializers for the contentstore v2 utils views module.

This module contains DRF serializers for different utils like validations.
"""

from rest_framework import serializers


class NumericalInputValidationRequestSerializer(serializers.Serializer):
    formula = serializers.CharField()


class NumericalInputValidationReponseSerializer(serializers.Serializer):
    preview = serializers.CharField()
    is_valid = serializers.BooleanField()
    error = serializers.CharField(allow_null=True)
