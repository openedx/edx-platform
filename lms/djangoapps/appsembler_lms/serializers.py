from rest_framework import serializers


class UserSignupSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    email = serializers.EmailField(max_length=200)
    password = serializers.CharField(max_length=200)
    org = serializers.CharField(max_length=100)
    org_name = serializers.CharField(max_length=200)
    secret_key = serializers.CharField(max_length=100)
    course_id = serializers.CharField(max_length=200, required=False)
