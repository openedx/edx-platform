from rest_framework import serializers
from drf_compound_fields import fields as compound_fields


class UserSignupSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=200)
    last_name = serializers.CharField(max_length=200)
    email = serializers.EmailField(max_length=200)
    password = serializers.CharField(max_length=200)
    secret_key = serializers.CharField(max_length=100)
    courses = compound_fields.ListField(serializers.IntegerField(), required=False)
