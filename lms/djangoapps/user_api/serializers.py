from django.contrib.auth.models import User
from rest_framework import serializers
from student.models import UserProfile
from user_api.models import UserPreference


class UserSerializer(serializers.HyperlinkedModelSerializer):
    name = serializers.SerializerMethodField("get_name")

    def get_name(self, user):
        profile = UserProfile.objects.get(user=user)
        return profile.name

    class Meta:
        model = User
        # This list is the minimal set required by the notification service
        fields = ("id", "email", "name", "username")
        read_only_fields = ("id", "email", "username")


class UserPreferenceSerializer(serializers.HyperlinkedModelSerializer):
    user = UserSerializer()

    class Meta:
        model = UserPreference
        depth = 1
