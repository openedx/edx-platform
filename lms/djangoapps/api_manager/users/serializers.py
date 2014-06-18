""" Django REST Framework Serializers """

from api_manager.models import APIUser
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    """ Serializer for User model interactions """
    class Meta:
        """ Serializer/field specification """
        model = APIUser
        fields = ("id", "email", "username", "first_name", "last_name")
        read_only_fields = ("id", "email", "username")
