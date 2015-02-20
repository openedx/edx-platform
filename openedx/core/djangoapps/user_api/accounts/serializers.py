from rest_framework import serializers
from django.contrib.auth.models import User
from student.models import UserProfile


class AccountUserSerializer(serializers.HyperlinkedModelSerializer):
    """
    Class that serializes the portion of User model needed for account information.
    """
    class Meta:
        model = User
        fields = ("username", "email", "date_joined")
        read_only_fields = ("username", "email", "date_joined")


class AccountLegacyProfileSerializer(serializers.HyperlinkedModelSerializer):
    """
    Class that serializes the portion of UserProfile model needed for account information.
    """
    class Meta:
        model = UserProfile
        fields = (
            "name", "gender", "goals", "year_of_birth", "level_of_education", "language", "city", "country",
            "mailing_address"
        )
        read_only_fields = ("name",)
