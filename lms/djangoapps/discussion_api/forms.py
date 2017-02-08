"""
Discussion API forms
"""
from django.core.exceptions import ValidationError
from django.forms import (
    BooleanField,
    CharField,
    ChoiceField,
    Form,
    IntegerField,
)

from opaque_keys import InvalidKeyError
from opaque_keys.edx.locator import CourseLocator
from openedx.core.djangoapps.util.forms import MultiValueField, ExtendedNullBooleanField


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
            raise ValidationError("'{}' is not a valid course id".format(value))

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
                "The following query parameters are mutually exclusive: {}".format(
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
