"""
Discussion API serializers
"""
from urllib import urlencode
from urlparse import urlunparse

from django.contrib.auth.models import User as DjangoUser
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse

from rest_framework import serializers

from discussion_api.permissions import (
    NON_UPDATABLE_COMMENT_FIELDS,
    NON_UPDATABLE_THREAD_FIELDS,
    get_editable_fields,
)
from discussion_api.render import render_body
from django_comment_client.utils import is_comment_too_deep
from django_comment_common.models import (
    FORUM_ROLE_ADMINISTRATOR,
    FORUM_ROLE_COMMUNITY_TA,
    FORUM_ROLE_MODERATOR,
    Role,
)
from lms.lib.comment_client.comment import Comment
from lms.lib.comment_client.thread import Thread
from lms.lib.comment_client.user import User as CommentClientUser
from lms.lib.comment_client.utils import CommentClientRequestError
from openedx.core.djangoapps.course_groups.cohorts import get_cohort_names
from openedx.core.lib.api.fields import NonEmptyCharField


def get_context(course, request, thread=None):
    """
    Returns a context appropriate for use with ThreadSerializer or
    (if thread is provided) CommentSerializer.
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
    requester = request.user
    cc_requester = CommentClientUser.from_django_user(requester).retrieve()
    cc_requester["course_id"] = course.id
    return {
        "course": course,
        "request": request,
        "thread": thread,
        # For now, the only groups are cohorts
        "group_ids_to_names": get_cohort_names(course),
        "is_requester_privileged": requester.id in staff_user_ids or requester.id in ta_user_ids,
        "staff_user_ids": staff_user_ids,
        "ta_user_ids": ta_user_ids,
        "cc_requester": cc_requester,
    }


class _ContentSerializer(serializers.Serializer):
    """A base class for thread and comment serializers."""
    id_ = serializers.CharField(read_only=True)
    author = serializers.SerializerMethodField("get_author")
    author_label = serializers.SerializerMethodField("get_author_label")
    created_at = serializers.CharField(read_only=True)
    updated_at = serializers.CharField(read_only=True)
    raw_body = NonEmptyCharField(source="body")
    rendered_body = serializers.SerializerMethodField("get_rendered_body")
    abuse_flagged = serializers.SerializerMethodField("get_abuse_flagged")
    voted = serializers.SerializerMethodField("get_voted")
    vote_count = serializers.SerializerMethodField("get_vote_count")
    editable_fields = serializers.SerializerMethodField("get_editable_fields")

    non_updatable_fields = set()

    def __init__(self, *args, **kwargs):
        super(_ContentSerializer, self).__init__(*args, **kwargs)
        # id is an invalid class attribute name, so we must declare a different
        # name above and modify it here
        self.fields["id"] = self.fields.pop("id_")

        for field in self.non_updatable_fields:
            setattr(self, "validate_{}".format(field), self._validate_non_updatable)

    def _validate_non_updatable(self, attrs, _source):
        """Ensure that a field is not edited in an update operation."""
        if self.object:
            raise ValidationError("This field is not allowed in an update.")
        return attrs

    def _is_user_privileged(self, user_id):
        """
        Returns a boolean indicating whether the given user_id identifies a
        privileged user.
        """
        return user_id in self.context["staff_user_ids"] or user_id in self.context["ta_user_ids"]

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

    def get_rendered_body(self, obj):
        """Returns the rendered body content."""
        return render_body(obj["body"])

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

    def get_editable_fields(self, obj):
        """Return the list of the fields the requester can edit"""
        return sorted(get_editable_fields(obj, self.context))


class ThreadSerializer(_ContentSerializer):
    """
    A serializer for thread data.

    N.B. This should not be used with a comment_client Thread object that has
    not had retrieve() called, because of the interaction between DRF's attempts
    at introspection and Thread's __getattr__.
    """
    course_id = serializers.CharField()
    topic_id = NonEmptyCharField(source="commentable_id")
    group_id = serializers.IntegerField(required=False)
    group_name = serializers.SerializerMethodField("get_group_name")
    type_ = serializers.ChoiceField(
        source="thread_type",
        choices=[(val, val) for val in ["discussion", "question"]]
    )
    title = NonEmptyCharField()
    pinned = serializers.BooleanField(read_only=True)
    closed = serializers.BooleanField(read_only=True)
    following = serializers.SerializerMethodField("get_following")
    comment_count = serializers.IntegerField(source="comments_count", read_only=True)
    unread_comment_count = serializers.IntegerField(source="unread_comments_count", read_only=True)
    comment_list_url = serializers.SerializerMethodField("get_comment_list_url")
    endorsed_comment_list_url = serializers.SerializerMethodField("get_endorsed_comment_list_url")
    non_endorsed_comment_list_url = serializers.SerializerMethodField("get_non_endorsed_comment_list_url")

    non_updatable_fields = NON_UPDATABLE_THREAD_FIELDS

    def __init__(self, *args, **kwargs):
        super(ThreadSerializer, self).__init__(*args, **kwargs)
        # type is an invalid class attribute name, so we must declare a
        # different name above and modify it here
        self.fields["type"] = self.fields.pop("type_")
        # Compensate for the fact that some threads in the comments service do
        # not have the pinned field set
        if self.object and self.object.get("pinned") is None:
            self.object["pinned"] = False

    def get_group_name(self, obj):
        """Returns the name of the group identified by the thread's group_id."""
        return self.context["group_ids_to_names"].get(obj["group_id"])

    def get_following(self, obj):
        """
        Returns a boolean indicating whether the requester is following the
        thread.
        """
        return obj["id"] in self.context["cc_requester"]["subscribed_thread_ids"]

    def get_comment_list_url(self, obj, endorsed=None):
        """
        Returns the URL to retrieve the thread's comments, optionally including
        the endorsed query parameter.
        """
        if (
                (obj["thread_type"] == "question" and endorsed is None) or
                (obj["thread_type"] == "discussion" and endorsed is not None)
        ):
            return None
        path = reverse("comment-list")
        query_dict = {"thread_id": obj["id"]}
        if endorsed is not None:
            query_dict["endorsed"] = endorsed
        return self.context["request"].build_absolute_uri(
            urlunparse(("", "", path, "", urlencode(query_dict), ""))
        )

    def get_endorsed_comment_list_url(self, obj):
        """Returns the URL to retrieve the thread's endorsed comments."""
        return self.get_comment_list_url(obj, endorsed=True)

    def get_non_endorsed_comment_list_url(self, obj):
        """Returns the URL to retrieve the thread's non-endorsed comments."""
        return self.get_comment_list_url(obj, endorsed=False)

    def restore_object(self, attrs, instance=None):
        if instance:
            for key, val in attrs.items():
                instance[key] = val
            return instance
        else:
            return Thread(user_id=self.context["cc_requester"]["id"], **attrs)


class CommentSerializer(_ContentSerializer):
    """
    A serializer for comment data.

    N.B. This should not be used with a comment_client Comment object that has
    not had retrieve() called, because of the interaction between DRF's attempts
    at introspection and Comment's __getattr__.
    """
    thread_id = serializers.CharField()
    parent_id = serializers.CharField(required=False)
    endorsed = serializers.BooleanField(required=False)
    endorsed_by = serializers.SerializerMethodField("get_endorsed_by")
    endorsed_by_label = serializers.SerializerMethodField("get_endorsed_by_label")
    endorsed_at = serializers.SerializerMethodField("get_endorsed_at")
    children = serializers.SerializerMethodField("get_children")

    non_updatable_fields = NON_UPDATABLE_COMMENT_FIELDS

    def get_endorsed_by(self, obj):
        """
        Returns the username of the endorsing user, if the information is
        available and would not identify the author of an anonymous thread.
        """
        endorsement = obj.get("endorsement")
        if endorsement:
            endorser_id = int(endorsement["user_id"])
            # Avoid revealing the identity of an anonymous non-staff question
            # author who has endorsed a comment in the thread
            if not (
                    self._is_anonymous(self.context["thread"]) and
                    not self._is_user_privileged(endorser_id)
            ):
                return DjangoUser.objects.get(id=endorser_id).username
        return None

    def get_endorsed_by_label(self, obj):
        """
        Returns the role label (i.e. "staff" or "community_ta") for the
        endorsing user
        """
        endorsement = obj.get("endorsement")
        if endorsement:
            return self._get_user_label(int(endorsement["user_id"]))
        else:
            return None

    def get_endorsed_at(self, obj):
        """Returns the timestamp for the endorsement, if available."""
        endorsement = obj.get("endorsement")
        return endorsement["time"] if endorsement else None

    def get_children(self, obj):
        return [
            CommentSerializer(child, context=self.context).data
            for child in obj.get("children", [])
        ]

    def validate(self, attrs):
        """
        Ensure that parent_id identifies a comment that is actually in the
        thread identified by thread_id and does not violate the configured
        maximum depth.
        """
        parent = None
        parent_id = attrs.get("parent_id")
        if parent_id:
            try:
                parent = Comment(id=parent_id).retrieve()
            except CommentClientRequestError:
                pass
            if not (parent and parent["thread_id"] == attrs["thread_id"]):
                raise ValidationError(
                    "parent_id does not identify a comment in the thread identified by thread_id."
                )
        if is_comment_too_deep(parent):
            raise ValidationError({"parent_id": ["Comment level is too deep."]})
        return attrs

    def restore_object(self, attrs, instance=None):
        if instance:
            for key, val in attrs.items():
                instance[key] = val
                # TODO: The comments service doesn't populate the endorsement
                # field on comment creation, so we only provide
                # endorsement_user_id on update
                if key == "endorsed":
                    instance["endorsement_user_id"] = self.context["cc_requester"]["id"]
            return instance
        return Comment(
            course_id=self.context["thread"]["course_id"],
            user_id=self.context["cc_requester"]["id"],
            **attrs
        )
