"""
    Serializer for user API
"""
from rest_framework import serializers
from django.core.validators import RegexValidator


class GroupSerializer(serializers.Serializer):
    """
    Serializes facebook groups request
    """
    name = serializers.CharField(max_length=150)
    description = serializers.CharField(max_length=200, required=False)
    privacy = serializers.ChoiceField(choices=[("open", "open"), ("closed", "closed")], required=False)


class GroupsMembersSerializer(serializers.Serializer):
    """
    Serializes facebook invitations request
    """
    member_ids = serializers.CharField(
        required=True,
        validators=[
            RegexValidator(
                regex=r'^([\d]+,?)*$',
                message='A comma separated list of member ids must be provided',
                code='member_ids error'
            ),
        ]
    )
