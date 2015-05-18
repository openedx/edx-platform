"""
Discussion API serializers
"""
from rest_framework import serializers

from django_comment_common.models import (
    FORUM_ROLE_ADMINISTRATOR,
    FORUM_ROLE_COMMUNITY_TA,
    FORUM_ROLE_MODERATOR,
    Role,
)
from lms.lib.comment_client.user import User
from openedx.core.djangoapps.course_groups.cohorts import get_cohort_names


def get_context(course, requester):
    """
    Returns a context appropriate for use with ThreadSerializer or
    CommentSerializer.
    """
    # TODO: cache staff_user_ids and ta_user_ids if we need to improve perf
    staff_user_ids = {
        user.id
        for role in Role.objects.filter(
            name__in=[FORUM_ROLE_ADMINISTRATOR, FORUM_ROLE_MODERATOR],
            course_id=course.id
        )
        for user in role.users.all()
    }
    ta_user_ids = {
        user.id
        for role in Role.objects.filter(name=FORUM_ROLE_COMMUNITY_TA, course_id=course.id)
        for user in role.users.all()
    }
    return {
        # For now, the only groups are cohorts
        "group_ids_to_names": get_cohort_names(course),
        "is_requester_privileged": requester.id in staff_user_ids or requester.id in ta_user_ids,
        "staff_user_ids": staff_user_ids,
        "ta_user_ids": ta_user_ids,
        "cc_requester": User.from_django_user(requester).retrieve(),
    }


class _ContentSerializer(serializers.Serializer):
    """A base class for thread and comment serializers."""
    id_ = serializers.CharField(read_only=True)
    author = serializers.SerializerMethodField("get_author")
    author_label = serializers.SerializerMethodField("get_author_label")
    created_at = serializers.CharField(read_only=True)
    updated_at = serializers.CharField(read_only=True)
    raw_body = serializers.CharField(source="body")
    abuse_flagged = serializers.SerializerMethodField("get_abuse_flagged")
    voted = serializers.SerializerMethodField("get_voted")
    vote_count = serializers.SerializerMethodField("get_vote_count")

    def __init__(self, *args, **kwargs):
        super(_ContentSerializer, self).__init__(*args, **kwargs)
        # id is an invalid class attribute name, so we must declare a different
        # name above and modify it here
        self.fields["id"] = self.fields.pop("id_")

    def _is_anonymous(self, obj):
        """
        Returns a boolean indicating whether the content should be anonymous to
        the requester.
        """
        return (
            obj["anonymous"] or
            obj["anonymous_to_peers"] and not self.context["is_requester_privileged"]
        )

    def get_author(self, obj):
        """Returns the author's username, or None if the content is anonymous."""
        return None if self._is_anonymous(obj) else obj["username"]

    def _get_user_label(self, user_id):
        """
        Returns the role label (i.e. "staff" or "community_ta") for the user
        with the given id.
        """
        return (
            "staff" if user_id in self.context["staff_user_ids"] else
            "community_ta" if user_id in self.context["ta_user_ids"] else
            None
        )

    def get_author_label(self, obj):
        """Returns the role label for the content author."""
        return None if self._is_anonymous(obj) else self._get_user_label(int(obj["user_id"]))

    def get_abuse_flagged(self, obj):
        """
        Returns a boolean indicating whether the requester has flagged the
        content as abusive.
        """
        return self.context["cc_requester"]["id"] in obj["abuse_flaggers"]

    def get_voted(self, obj):
        """
        Returns a boolean indicating whether the requester has voted for the
        content.
        """
        return obj["id"] in self.context["cc_requester"]["upvoted_ids"]

    def get_vote_count(self, obj):
        """Returns the number of votes for the content."""
        return obj["votes"]["up_count"]


class ThreadSerializer(_ContentSerializer):
    """
    A serializer for thread data.

    N.B. This should not be used with a comment_client Thread object that has
    not had retrieve() called, because of the interaction between DRF's attempts
    at introspection and Thread's __getattr__.
    """
    course_id = serializers.CharField()
    topic_id = serializers.CharField(source="commentable_id")
    group_id = serializers.IntegerField()
    group_name = serializers.SerializerMethodField("get_group_name")
    type_ = serializers.ChoiceField(source="thread_type", choices=("discussion", "question"))
    title = serializers.CharField()
    pinned = serializers.BooleanField()
    closed = serializers.BooleanField()
    following = serializers.SerializerMethodField("get_following")
    comment_count = serializers.IntegerField(source="comments_count")
    unread_comment_count = serializers.IntegerField(source="unread_comments_count")

    def __init__(self, *args, **kwargs):
        super(ThreadSerializer, self).__init__(*args, **kwargs)
        # type is an invalid class attribute name, so we must declare a
        # different name above and modify it here
        self.fields["type"] = self.fields.pop("type_")

    def get_group_name(self, obj):
        """Returns the name of the group identified by the thread's group_id."""
        return self.context["group_ids_to_names"].get(obj["group_id"])

    def get_following(self, obj):
        """
        Returns a boolean indicating whether the requester is following the
        thread.
        """
        return obj["id"] in self.context["cc_requester"]["subscribed_thread_ids"]


class CommentSerializer(_ContentSerializer):
    """
    A serializer for comment data.

    N.B. This should not be used with a comment_client Comment object that has
    not had retrieve() called, because of the interaction between DRF's attempts
    at introspection and Comment's __getattr__.
    """
    thread_id = serializers.CharField()
    parent_id = serializers.SerializerMethodField("get_parent_id")
    children = serializers.SerializerMethodField("get_children")

    def get_parent_id(self, _obj):
        """Returns the comment's parent's id (taken from the context)."""
        return self.context.get("parent_id")

    def get_children(self, obj):
        """Returns the list of the comment's children, serialized."""
        child_context = dict(self.context)
        child_context["parent_id"] = obj["id"]
        return [CommentSerializer(child, context=child_context).data for child in obj["children"]]
