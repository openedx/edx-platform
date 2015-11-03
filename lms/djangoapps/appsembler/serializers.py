from rest_framework import serializers
from drf_compound_fields import fields as compound_fields


class UserSignupSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=200)
    last_name = serializers.CharField(max_length=200)
    email = serializers.EmailField(max_length=200)
    password = serializers.CharField(max_length=200)
    secret_key = serializers.CharField(max_length=100)
    course_id = serializers.CharField(max_length=200, required=False)
    full_name = serializers.SerializerMethodField('get_full_name')

    def get_full_name(self, obj):
        return u"{0} {1}".format(obj.get('first_name'), obj.get('last_name'))
