from rest_framework import serializers
from django.contrib.auth.models import User
from student.models import UserProfile
from openedx.core.djangoapps.user_api.accounts import NAME_MIN_LENGTH


class AccountUserSerializer(serializers.HyperlinkedModelSerializer):
    """
    Class that serializes the portion of User model needed for account information.
    """
    class Meta:
        model = User
        fields = ("username", "email", "date_joined", "is_active")
        read_only_fields = ("username", "email", "date_joined", "is_active")


class AccountLegacyProfileSerializer(serializers.HyperlinkedModelSerializer):
    """
    Class that serializes the portion of UserProfile model needed for account information.
    """
    class Meta:
        model = UserProfile
        fields = (
            "name", "gender", "goals", "year_of_birth", "level_of_education", "language", "country", "mailing_address"
        )
        # Currently no read-only field, but keep this so view code doesn't need to know.
        read_only_fields = ()

    def validate_name(self, attrs, source):
        """ Enforce minimum length for name. """
        if source in attrs:
            new_name = attrs[source].strip()
            if len(new_name) < NAME_MIN_LENGTH:
                raise serializers.ValidationError(
                    "The name field must be at least {} characters long.".format(NAME_MIN_LENGTH)
                )
            attrs[source] = new_name

        return attrs

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
