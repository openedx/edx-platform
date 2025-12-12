"""
Django REST Framework serializers for the User API application
"""


from django.core.exceptions import ValidationError
from django.contrib.auth.models import User  # lint-amnesty, pylint: disable=imported-auth-user
from rest_framework import serializers

from common.djangoapps.student.models import UserProfile, email_exists_or_retired
from lms.djangoapps.verify_student.models import (
    ManualVerification,
    SoftwareSecurePhotoVerification
)

from .models import UserPreference


class UserSerializer(serializers.HyperlinkedModelSerializer):
    """
    Serializer that generates a representation of a User entity containing a subset of fields
    """
    name = serializers.SerializerMethodField()
    preferences = serializers.SerializerMethodField()

    def get_name(self, user):
        """
        Return the name attribute from the user profile object if profile exists else none
        """
        return user.profile.name

    def get_preferences(self, user):
        """
        Returns the set of preferences as a dict for the specified user
        """
        return UserPreference.get_all_preferences(user)

    class Meta:
        model = User
        # This list is the minimal set required by the notification service
        fields = ("id", "url", "email", "name", "username", "preferences")
        read_only_fields = ("id", "email", "username")
        # For disambiguating within the drf-yasg swagger schema
        ref_name = 'user_api.User'


class UserPreferenceSerializer(serializers.HyperlinkedModelSerializer):
    """
    Serializer that generates a representation of a UserPreference entity.
    """
    user = UserSerializer()

    class Meta:
        model = UserPreference
        depth = 1
        fields = ('user', 'key', 'value', 'url')


class RawUserPreferenceSerializer(serializers.ModelSerializer):
    """
    Serializer that generates a raw representation of a user preference.
    """
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = UserPreference
        depth = 1
        fields = ('user', 'key', 'value', 'url')


class ReadOnlyFieldsSerializerMixin:
    """
    Mixin for use with Serializers that provides a method
    `get_read_only_fields`, which returns a tuple of all read-only
    fields on the Serializer.
    """
    @classmethod
    def get_read_only_fields(cls):
        """
        Return all fields on this Serializer class which are read-only.
        Expects sub-classes implement Meta.explicit_read_only_fields,
        which is a tuple declaring read-only fields which were declared
        explicitly and thus could not be added to the usual
        cls.Meta.read_only_fields tuple.
        """
        return getattr(cls.Meta, 'read_only_fields', '') + getattr(cls.Meta, 'explicit_read_only_fields', '')

    @classmethod
    def get_writeable_fields(cls):
        """
        Return all fields on this serializer that are writeable.
        """
        all_fields = getattr(cls.Meta, 'fields', tuple())
        return tuple(set(all_fields) - set(cls.get_read_only_fields()))


class CountryTimeZoneSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """
    Serializer that generates a list of common time zones for a country
    """
    time_zone = serializers.CharField()
    description = serializers.CharField()


class IDVerificationDetailsSerializer(serializers.Serializer):  # lint-amnesty, pylint: disable=abstract-method, missing-class-docstring
    type = serializers.SerializerMethodField()
    status = serializers.CharField()
    expiration_datetime = serializers.DateTimeField()
    message = serializers.SerializerMethodField()
    updated_at = serializers.DateTimeField()
    receipt_id = serializers.SerializerMethodField()

    def get_type(self, obj):  # lint-amnesty, pylint: disable=missing-function-docstring
        if isinstance(obj, SoftwareSecurePhotoVerification):
            return 'Software Secure'
        elif isinstance(obj, ManualVerification):
            return 'Manual'
        else:
            return 'SSO'

    def get_message(self, obj):  # lint-amnesty, pylint: disable=missing-function-docstring
        if isinstance(obj, SoftwareSecurePhotoVerification):
            return obj.error_msg
        elif isinstance(obj, ManualVerification):
            return obj.reason
        else:
            return ''

    def get_receipt_id(self, obj):
        if isinstance(obj, SoftwareSecurePhotoVerification):
            return obj.receipt_id
        else:
            return None


class UserCreateSerializer(serializers.HyperlinkedModelSerializer):
    """
    Class that serializes the information of a new User model.

    Update and validate User information.
    """

    class Meta(object):
        """
        Meta class for `UserSerializer`.
        """

        model = User
        fields = '__all__'
        read_only_fields = ('password', 'username')

    def update(self, instance, validated_data):
        """
        Update User instance by the data dictionary.

        Method updates User instance if data is correct.
        :param instance: User instance.
        :param validated_data: Dictionary with user's data.
        :return: User instance.
        """
        if not isinstance(instance, User):
            raise ValidationError("The instance must be the User type.")

        if isinstance(validated_data, dict):
            username = validated_data.get("username")
            if username and (instance.username != username):
                instance.username = self._validate_username(validated_data)
            email = validated_data.get("email")
            if email and (instance.email != email):
                self._check_email_unique(email)

            validated_data = self.run_validation(validated_data)
            for field_name, field_value in validated_data.items():
                setattr(instance, field_name, field_value)
            instance.save()
        else:
            raise ValidationError("The data must be the Dictionary type.")
        return instance

    @staticmethod
    def _validate_username(data):
        """
        Validate username filed in User object.

        :param data: Dictionary with key username
        :return: The username value
        """
        validate_data = UserUsernameSerializer().run_validation(data)
        return validate_data.get("username")

    @staticmethod
    def _check_email_unique(email):
        if email_exists_or_retired(email=email):
            raise ValidationError("User already exists with this email")


class UserUsernameSerializer(serializers.HyperlinkedModelSerializer):
    """
    Class that serializes the information of User model.

    Validate user's username.
    """

    class Meta(object):
        """
        Meta class for `UserUsernameSerializer`.
        """

        model = User
        fields = ('username',)


class ProfileSerializer(serializers.HyperlinkedModelSerializer):
    """
    Class that serializes the information of UserProfile model.

    Update and validate User information.
    """

    class Meta(object):
        """
        Meta class for `ProfileSerializer`.
        """

        model = UserProfile
        exclude = ('user',)
        read_only_fields = ('user', 'language_proficiencies')
        explicit_read_only_fields = tuple()

    def update(self, instance, validated_data):
        """
        Update user profile object with validated data.
        """
        if not isinstance(instance, UserProfile):
            raise ValidationError("The instance must be the UserProfile type.")
        if isinstance(validated_data, dict):
            validated_data = self.run_validation(validated_data)
            for field_name, field_value in validated_data.items():
                setattr(instance, field_name, field_value)
            instance.save()
        else:
            raise ValidationError("The data must be the Dictionary type.")
        print(instance.__dict__)
        return instance
