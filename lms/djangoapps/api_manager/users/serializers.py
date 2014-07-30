""" Django REST Framework Serializers """

from api_manager.models import APIUser
from rest_framework import serializers
from api_manager.organizations.serializers import BasicOrganizationSerializer


class UserSerializer(serializers.ModelSerializer):
    """ Serializer for User model interactions """
    organizations = BasicOrganizationSerializer(many=True, required=False)
    created = serializers.DateTimeField(source='date_joined', required=False)

    class Meta:
        """ Serializer/field specification """
        model = APIUser
        fields = ("id", "email", "username", "first_name", "last_name", "created", "is_active", "organizations")
        read_only_fields = ("id", "email", "username")


class UserCountByCitySerializer(serializers.Serializer):
    """ Serializer for user count by city """
    city = serializers.CharField(source='profile__city')
    count = serializers.IntegerField()


class UserRolesSerializer(serializers.Serializer):
    """ Serializer for user roles """
    course_id = serializers.CharField(source='course_id')
    role = serializers.CharField(source='role')
