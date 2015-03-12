from django.contrib.auth.models import User
from rest_framework import serializers
from student.models import UserProfile

from .models import UserPreference


class UserSerializer(serializers.HyperlinkedModelSerializer):
    name = serializers.SerializerMethodField("get_name")
    preferences = serializers.SerializerMethodField("get_preferences")

    def get_name(self, user):
        profile = UserProfile.objects.get(user=user)
        return profile.name

    def get_preferences(self, user):
        return dict([(pref.key, pref.value) for pref in user.preferences.all()])

    class Meta:
        model = User
        # This list is the minimal set required by the notification service
        fields = ("id", "url", "email", "name", "username", "preferences")
        read_only_fields = ("id", "email", "username")


class UserPreferenceSerializer(serializers.HyperlinkedModelSerializer):
    user = UserSerializer()

    class Meta:
        model = UserPreference
        depth = 1


class RawUserPreferenceSerializer(serializers.ModelSerializer):
    """Serializer that generates a raw representation of a user preference.
    """
    user = serializers.PrimaryKeyRelatedField()

    class Meta:
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
