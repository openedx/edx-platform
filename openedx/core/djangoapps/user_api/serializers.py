"""
Django REST Framework serializers for the User API application
"""
from django.contrib.auth.models import User
from django.utils.timezone import now
from rest_framework import serializers

from lms.djangoapps.verify_student.models import SoftwareSecurePhotoVerification
from student.models import UserProfile

from .models import UserPreference


class UserSerializer(serializers.HyperlinkedModelSerializer):
    """
    Serializer that generates a representation of a User entity containing a subset of fields
    """
    name = serializers.SerializerMethodField()
    preferences = serializers.SerializerMethodField()

    def get_name(self, user):
        """
        Return the name attribute from the user profile object
        """
        profile = UserProfile.objects.get(user=user)
        return profile.name

    def get_preferences(self, user):
        """
        Returns the set of preferences as a dict for the specified user
        """
        return dict([(pref.key, pref.value) for pref in user.preferences.all()])

    class Meta(object):
        model = User
        # This list is the minimal set required by the notification service
        fields = ("id", "url", "email", "name", "username", "preferences")
        read_only_fields = ("id", "email", "username")


class UserPreferenceSerializer(serializers.HyperlinkedModelSerializer):
    """
    Serializer that generates a represenation of a UserPreference entity
    """
    user = UserSerializer()

    class Meta(object):
        model = UserPreference
        depth = 1


class RawUserPreferenceSerializer(serializers.ModelSerializer):
    """
    Serializer that generates a raw representation of a user preference.
    """
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta(object):
        model = UserPreference
        depth = 1


class ReadOnlyFieldsSerializerMixin(object):
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


class SoftwareSecurePhotoVerificationSerializer(serializers.ModelSerializer):
    """
    Serializer that generates a representation of a user's photo verification status.
    """
    is_verified = serializers.SerializerMethodField()

    def get_is_verified(self, obj):
        """
        Return a boolean indicating if a the user is verified.
        """
        return obj.status == 'approved' and obj.expiration_datetime > now()

    class Meta(object):
        fields = ('status', 'expiration_datetime', 'is_verified')
        model = SoftwareSecurePhotoVerification
