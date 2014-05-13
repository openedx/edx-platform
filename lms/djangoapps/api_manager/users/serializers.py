""" Django REST Framework Serializers """

from django.contrib.auth.models import User

from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    """ Serializer for User model interactions """
    class Meta:
        """ Serializer/field specification """
        model = User
        fields = ("id", "email", "username", "first_name", "last_name")
        read_only_fields = ("id", "email", "username")
