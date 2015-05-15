"""Defines serializers used by the Team API."""

from django.contrib.auth.models import User
from rest_framework import serializers
from openedx.core.lib.api.serializers import CollapsedReferenceSerializer
from openedx.core.lib.api.fields import ExpandableField
from .models import CourseTeam, CourseTeamMembership
from openedx.core.djangoapps.user_api.serializers import UserSerializer


class UserMembershipSerializer(serializers.ModelSerializer):
    """Serializes CourseTeamMemberships with only user and date_joined

    Used for listing team members.
    """
    user = ExpandableField(
        collapsed_serializer=CollapsedReferenceSerializer(
            model_class=User,
            id_source='username',
            view_name='accounts_api',
            read_only=True,
        ),
        expanded_serializer=UserSerializer(),
    )

    class Meta(object):
        """Defines meta information for the ModelSerializer."""
        model = CourseTeamMembership
        fields = ("user", "date_joined")
        read_only_fields = ("date_joined",)


class CourseTeamSerializer(serializers.ModelSerializer):
    """Serializes a CourseTeam with membership information."""
    id = serializers.CharField(source='team_id', read_only=True)  # pylint: disable=invalid-name
    membership = UserMembershipSerializer(many=True, read_only=True)

    class Meta(object):
        """Defines meta information for the ModelSerializer."""
        model = CourseTeam
        fields = (
            "id",
            "name",
            "is_active",
            "course_id",
            "topic_id",
            "date_created",
            "description",
            "country",
            "language",
            "membership",
        )
        read_only_fields = ("course_id", "date_created")


class CourseTeamCreationSerializer(serializers.ModelSerializer):
    """Deserializes a CourseTeam for creation."""

    class Meta(object):
        """Defines meta information for the ModelSerializer."""
        model = CourseTeam
        fields = (
            "name",
            "course_id",
            "description",
            "topic_id",
            "country",
            "language",
        )

    def restore_object(self, attrs, instance=None):
        """Restores a CourseTeam instance from the given attrs."""
        return CourseTeam.create(
            name=attrs.get("name", ''),
            course_id=attrs.get("course_id"),
            description=attrs.get("description", ''),
            topic_id=attrs.get("topic_id", ''),
            country=attrs.get("country", ''),
            language=attrs.get("language", ''),
        )


class MembershipSerializer(serializers.ModelSerializer):
    """Serializes CourseTeamMemberships with information about both teams and users."""
    user = ExpandableField(
        collapsed_serializer=CollapsedReferenceSerializer(
            model_class=User,
            id_source='username',
            view_name='accounts_api',
            read_only=True,
        ),
        expanded_serializer=UserSerializer(read_only=True)
    )
    team = ExpandableField(
        collapsed_serializer=CollapsedReferenceSerializer(
            model_class=CourseTeam,
            id_source='team_id',
            view_name='teams_detail',
            read_only=True,
        ),
        expanded_serializer=CourseTeamSerializer(read_only=True)
    )

    class Meta(object):
        """Defines meta information for the ModelSerializer."""
        model = CourseTeamMembership
        fields = ("user", "team", "date_joined")
        read_only_fields = ("date_joined",)


class TopicSerializer(serializers.Serializer):
    """Serializes a topic."""
    description = serializers.CharField()
    name = serializers.CharField()
    id = serializers.CharField()  # pylint: disable=invalid-name
