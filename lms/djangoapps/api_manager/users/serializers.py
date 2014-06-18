""" Django REST Framework Serializers """

from api_manager.models import APIUser
from rest_framework import serializers
from api_manager.organizations.serializers import BasicOrganizationSerializer


class UserSerializer(serializers.ModelSerializer):
    """ Serializer for User model interactions """
    organizations = BasicOrganizationSerializer(many=True, required=False)

    class Meta:
        """ Serializer/field specification """
        model = APIUser
        fields = ("id", "email", "username", "first_name", "last_name", "organizations")
        read_only_fields = ("id", "email", "username")
