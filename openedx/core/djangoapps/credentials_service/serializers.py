"""
Serializers for data manipulated by the credentials service APIs.
"""
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from openedx.core.djangoapps.credentials_service.models import UserCredential


class UserCredentialSerializer(serializers.ModelSerializer):
    """ CreditProvider """
    class Meta(object):
        model = UserCredential
