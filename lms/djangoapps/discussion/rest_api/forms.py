"""
Discussion API forms
"""


import six.moves.urllib.error
import six.moves.urllib.parse
import six.moves.urllib.request
from django.core.exceptions import ValidationError
from django.forms import BooleanField, CharField, ChoiceField, Form, IntegerField
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locator import CourseLocator
from six import text_type

from lms.djangoapps.courseware.courses import get_course_with_access
from openedx.core.djangoapps.django_comment_common.models import (
    FORUM_ROLE_COMMUNITY_TA,
    FORUM_ROLE_GROUP_MODERATOR,
    FORUM_ROLE_MODERATOR,
    Role
)
from openedx.core.djangoapps.util.forms import ExtendedNullBooleanField, MultiValueField


class _PaginationForm(Form):
    """A form that includes pagination fields"""
    page = IntegerField(required=False, min_value=1)
    page_size = IntegerField(required=False, min_value=1)

    def clean_page(self):
        """Return given valid page or default of 1"""
        return self.cleaned_data.get("page") or 1

    def clean_page_size(self):
        """Return given valid page_size (capped at 100) or default of 10"""
        return min(self.cleaned_data.get("page_size") or 10, 100)


class ThreadListGetForm(_PaginationForm):
    """
    A form to validate query parameters in the thread list retrieval endpoint
    """
    EXCLUSIVE_PARAMS = ["topic_id", "text_search", "following"]

    course_id = CharField()
    topic_id = MultiValueField(required=False)
    text_search = CharField(required=False)
    following = ExtendedNullBooleanField(required=False)
    view = ChoiceField(
        choices=[(choice, choice) for choice in ["unread", "unanswered"]],
        required=False,
    )
    order_by = ChoiceField(
        choices=[(choice, choice) for choice in ["last_activity_at", "comment_count", "vote_count"]],
        required=False
    )
    order_direction = ChoiceField(
        choices=[(choice, choice) for choice in ["desc"]],
        required=False
    )
    requested_fields = MultiValueField(required=False)

    def clean_order_by(self):
        """Return a default choice"""
        return self.cleaned_data.get("order_by") or "last_activity_at"

    def clean_order_direction(self):
        """Return a default choice"""
        return self.cleaned_data.get("order_direction") or "desc"

    def clean_course_id(self):
        """Validate course_id"""
        value = self.cleaned_data["course_id"]
        try:
            return CourseLocator.from_string(value)
        except InvalidKeyError:
            raise ValidationError(u"'{}' is not a valid course id".format(value))

    def clean_following(self):
        """Validate following"""
        value = self.cleaned_data["following"]
        if value is False:
            raise ValidationError("The value of the 'following' parameter must be true.")
        else:
            return value

    def clean(self):
        cleaned_data = super(ThreadListGetForm, self).clean()
        exclusive_params_count = sum(
            1 for param in self.EXCLUSIVE_PARAMS if cleaned_data.get(param)
        )
        if exclusive_params_count > 1:
            raise ValidationError(
                u"The following query parameters are mutually exclusive: {}".format(
                    ", ".join(self.EXCLUSIVE_PARAMS)
                )
            )
        return cleaned_data


class ThreadActionsForm(Form):
    """
    A form to handle fields in thread creation/update that require separate
    interactions with the comments service.
    """
    following = BooleanField(required=False)
    voted = BooleanField(required=False)
    abuse_flagged = BooleanField(required=False)
    read = BooleanField(required=False)


class CommentListGetForm(_PaginationForm):
    """
    A form to validate query parameters in the comment list retrieval endpoint
    """
    thread_id = CharField()
    endorsed = ExtendedNullBooleanField(required=False)
    requested_fields = MultiValueField(required=False)


class CommentActionsForm(Form):
    """
    A form to handle fields in comment creation/update that require separate
    interactions with the comments service.
    """
    voted = BooleanField(required=False)
    abuse_flagged = BooleanField(required=False)


class CommentGetForm(_PaginationForm):
    """
    A form to validate query parameters in the comment retrieval endpoint
    """
    requested_fields = MultiValueField(required=False)


class CourseDiscussionSettingsForm(Form):
    """
    A form to validate the fields in the course discussion settings requests.
    """
    course_id = CharField()

    def __init__(self, *args, **kwargs):
        self.request_user = kwargs.pop('request_user')
        super(CourseDiscussionSettingsForm, self).__init__(*args, **kwargs)

    def clean_course_id(self):
        """Validate the 'course_id' value"""
        course_id = self.cleaned_data['course_id']
        try:
            course_key = CourseKey.from_string(course_id)
            self.cleaned_data['course'] = get_course_with_access(self.request_user, 'staff', course_key)
            self.cleaned_data['course_key'] = course_key
            return course_id
        except InvalidKeyError:
            raise ValidationError(u"'{}' is not a valid course key".format(text_type(course_id)))


class CourseDiscussionRolesForm(CourseDiscussionSettingsForm):
    """
    A form to validate the fields in the course discussion roles requests.
    """
    ROLE_CHOICES = (
        (FORUM_ROLE_MODERATOR, FORUM_ROLE_MODERATOR),
        (FORUM_ROLE_COMMUNITY_TA, FORUM_ROLE_MODERATOR),
        (FORUM_ROLE_GROUP_MODERATOR, FORUM_ROLE_GROUP_MODERATOR),
    )
    rolename = ChoiceField(
        choices=ROLE_CHOICES,
        error_messages={u"invalid_choice": u"Role '%(value)s' does not exist"}
    )

    def clean_rolename(self):
        """Validate the 'rolename' value."""
        rolename = six.moves.urllib.parse.unquote(self.cleaned_data.get('rolename'))
        course_id = self.cleaned_data.get('course_key')
        if course_id and rolename:
            try:
                role = Role.objects.get(name=rolename, course_id=course_id)
            except Role.DoesNotExist:
                raise ValidationError(u"Role '{}' does not exist".format(rolename))

            self.cleaned_data['role'] = role
            return rolename
