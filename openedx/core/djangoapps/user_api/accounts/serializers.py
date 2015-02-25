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
            "name", "gender", "goals", "year_of_birth", "level_of_education", "language", "country", "mailing_address"
        )
        read_only_fields = ("name",)

    def transform_gender(self, obj, value):
        """ Converts empty string to None, to indicate not set. Replaced by to_representation in version 3. """
        return AccountLegacyProfileSerializer.convert_empty_to_None(value)

    def transform_country(self, obj, value):
        """ Converts empty string to None, to indicate not set. Replaced by to_representation in version 3. """
        return AccountLegacyProfileSerializer.convert_empty_to_None(value)

    def transform_level_of_education(self, obj, value):
        """ Converts empty string to None, to indicate not set. Replaced by to_representation in version 3. """
        return AccountLegacyProfileSerializer.convert_empty_to_None(value)

    @staticmethod
    def convert_empty_to_None(value):
        """ Helper method to convert empty string to None (other values pass through). """
        return None if value == "" else value
