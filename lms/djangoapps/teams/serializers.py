"""Defines serializers used by the Team API."""
from copy import deepcopy
from django.contrib.auth.models import User
from django.db.models import Count
from django.conf import settings

from rest_framework import serializers

from openedx.core.lib.api.serializers import CollapsedReferenceSerializer, PaginationSerializer
from openedx.core.lib.api.fields import ExpandableField
from openedx.core.djangoapps.user_api.accounts.serializers import UserReadOnlySerializer

from .models import CourseTeam, CourseTeamMembership


class UserMembershipSerializer(serializers.ModelSerializer):
    """Serializes CourseTeamMemberships with only user and date_joined

    Used for listing team members.
    """
    profile_configuration = deepcopy(settings.ACCOUNT_VISIBILITY_CONFIGURATION)
    profile_configuration['shareable_fields'].append('url')
    profile_configuration['public_fields'].append('url')

    user = ExpandableField(
        collapsed_serializer=CollapsedReferenceSerializer(
            model_class=User,
            id_source='username',
            view_name='accounts_api',
            read_only=True,
        ),
        expanded_serializer=UserReadOnlySerializer(configuration=profile_configuration),
    )

    class Meta(object):
        """Defines meta information for the ModelSerializer."""
        model = CourseTeamMembership
        fields = ("user", "date_joined", "last_activity_at")
        read_only_fields = ("date_joined", "last_activity_at")


class CourseTeamSerializer(serializers.ModelSerializer):
    """Serializes a CourseTeam with membership information."""
    id = serializers.CharField(source='team_id', read_only=True)  # pylint: disable=invalid-name
    membership = UserMembershipSerializer(many=True, read_only=True)

    class Meta(object):
        """Defines meta information for the ModelSerializer."""
        model = CourseTeam
        fields = (
            "id",
            "discussion_topic_id",
            "name",
            "course_id",
            "topic_id",
            "date_created",
            "description",
            "country",
            "language",
            "last_activity_at",
            "membership",
        )
        read_only_fields = ("course_id", "date_created", "discussion_topic_id", "last_activity_at")


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


class CourseTeamSerializerWithoutMembership(CourseTeamSerializer):
    """The same as the `CourseTeamSerializer`, but elides the membership field.

    Intended to be used as a sub-serializer for serializing team
    memberships, since the membership field is redundant in that case.
    """

    def __init__(self, *args, **kwargs):
        super(CourseTeamSerializerWithoutMembership, self).__init__(*args, **kwargs)
        del self.fields['membership']


class MembershipSerializer(serializers.ModelSerializer):
    """Serializes CourseTeamMemberships with information about both teams and users."""
    profile_configuration = deepcopy(settings.ACCOUNT_VISIBILITY_CONFIGURATION)
    profile_configuration['shareable_fields'].append('url')
    profile_configuration['public_fields'].append('url')

    user = ExpandableField(
        collapsed_serializer=CollapsedReferenceSerializer(
            model_class=User,
            id_source='username',
            view_name='accounts_api',
            read_only=True,
        ),
        expanded_serializer=UserReadOnlySerializer(configuration=profile_configuration)
    )
    team = ExpandableField(
        collapsed_serializer=CollapsedReferenceSerializer(
            model_class=CourseTeam,
            id_source='team_id',
            view_name='teams_detail',
            read_only=True,
        ),
        expanded_serializer=CourseTeamSerializerWithoutMembership(read_only=True),
    )

    class Meta(object):
        """Defines meta information for the ModelSerializer."""
        model = CourseTeamMembership
        fields = ("user", "team", "date_joined", "last_activity_at")
        read_only_fields = ("date_joined", "last_activity_at")


class PaginatedMembershipSerializer(PaginationSerializer):
    """Serializes team memberships with support for pagination."""
    class Meta(object):
        """Defines meta information for the PaginatedMembershipSerializer."""
        object_serializer_class = MembershipSerializer


class BaseTopicSerializer(serializers.Serializer):
    """Serializes a topic without team_count."""
    description = serializers.CharField()
    name = serializers.CharField()
    id = serializers.CharField()  # pylint: disable=invalid-name


class TopicSerializer(BaseTopicSerializer):
    """
    Adds team_count to the basic topic serializer, checking if team_count
    is already present in the topic data, and if not, querying the CourseTeam
    model to get the count. Requires that `context` is provided with a valid course_id
    in order to filter teams within the course.
    """
    team_count = serializers.SerializerMethodField('get_team_count')

    def get_team_count(self, topic):
        """Get the number of teams associated with this topic"""
        # If team_count is already present (possible if topic data was pre-processed for sorting), return it.
        if 'team_count' in topic:
            return topic['team_count']
        else:
            return CourseTeam.objects.filter(course_id=self.context['course_id'], topic_id=topic['id']).count()


class PaginatedTopicSerializer(PaginationSerializer):
    """
    Serializes a set of topics, adding the team_count field to each topic individually, if team_count
    is not already present in the topic data. Requires that `context` is provided with a valid course_id in
    order to filter teams within the course.
    """
    class Meta(object):
        """Defines meta information for the PaginatedTopicSerializer."""
        object_serializer_class = TopicSerializer


class BulkTeamCountPaginatedTopicSerializer(PaginationSerializer):
    """
    Serializes a set of topics, adding the team_count field to each topic as a bulk operation per page
    (only on the page being returned). Requires that `context` is provided with a valid course_id in
    order to filter teams within the course.
    """
    class Meta(object):
        """Defines meta information for the BulkTeamCountPaginatedTopicSerializer."""
        object_serializer_class = BaseTopicSerializer

    def __init__(self, *args, **kwargs):
        """Adds team_count to each topic on the current page."""
        super(BulkTeamCountPaginatedTopicSerializer, self).__init__(*args, **kwargs)
        add_team_count(self.data['results'], self.context['course_id'])


def add_team_count(topics, course_id):
    """
    Helper method to add team_count for a list of topics.
    This allows for a more efficient single query.
    """
    topic_ids = [topic['id'] for topic in topics]
    teams_per_topic = CourseTeam.objects.filter(
        course_id=course_id,
        topic_id__in=topic_ids
    ).values('topic_id').annotate(team_count=Count('topic_id'))

    topics_to_team_count = {d['topic_id']: d['team_count'] for d in teams_per_topic}
    for topic in topics:
        topic['team_count'] = topics_to_team_count.get(topic['id'], 0)
