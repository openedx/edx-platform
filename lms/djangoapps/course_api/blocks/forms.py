"""

"""
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.forms import Form, CharField, ChoiceField, Field, MultipleHiddenInput
from django.http import Http404
from rest_framework.exceptions import PermissionDenied

from xmodule.modulestore.django import modulestore
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import UsageKey

from transformers.student_view import StudentViewTransformer
from transformers.block_counts import BlockCountsTransformer
from .permissions import can_access_other_users_blocks, can_access_users_blocks


class ListField(Field):
    """
    Field for a list of strings
    """
    widget = MultipleHiddenInput


class BlockListGetForm(Form):
    """
    A form to validate query parameters in the block list retrieval endpoint
    """
    user = CharField(required=True)  # TODO return all blocks if user is not specified by requesting staff user
    usage_key = CharField(required=True)
    requested_fields = ListField(required=False)
    student_view_data = ListField(required=False)
    block_counts = ListField(required=False)
    depth = CharField(required=False)
    return_type = ChoiceField(
        required=False,
        choices=[(choice, choice) for choice in ['dict', 'list']],
    )

    def clean_requested_fields(self):
        # add default requested_fields
        return set(self.cleaned_data['requested_fields'] or set()) | {'type', 'display_name'}

    def clean_depth(self):
        value = self.cleaned_data['depth']
        if not value:
            return 0
        elif value == "all":
            return None
        try:
            return int(value)
        except ValueError:
            raise ValidationError("'{}' is not a valid depth value.".format(value))

    def clean_usage_key(self):
        usage_key = self.cleaned_data['usage_key']

        try:
            usage_key = UsageKey.from_string(usage_key)
            usage_key = usage_key.replace(course_key=modulestore().fill_in_run(usage_key.course_key))
        except InvalidKeyError:
            raise ValidationError("'{}' is not a valid usage key.".format(unicode(usage_key)))

        return usage_key

    def clean_return_type(self):
        """
        Return valid 'return_type' or default value of 'dict'
        """
        return self.cleaned_data['return_type'] or 'dict'

    def clean_requested_user(self, cleaned_data, course_key):
        """
        Validates and returns the requested_user, while checking permissions.
        """
        requested_username = cleaned_data.get('user', '')
        requesting_user = self.initial['requesting_user']

        if requesting_user.username.lower() == requested_username.lower():
            requested_user = requesting_user
        else:
            # the requesting user is trying to access another user's view
            # verify requesting user can access another user's blocks
            if not can_access_other_users_blocks(requesting_user, course_key):
                raise PermissionDenied(
                    "'{requesting_username}' does not have permission to access view for '{requested_username}'."
                    .format(requesting_username=requesting_user.username, requested_username=requested_username)
                )

            # update requested user object
            try:
                requested_user = User.objects.get(username=requested_username)
            except (User.DoesNotExist):
                raise Http404("Requested user '{username}' does not exist.".format(username=requested_username))

        # verify whether the requested user's blocks can be accessed
        if not can_access_users_blocks(requested_user, course_key):
            raise PermissionDenied(
                "Course blocks for '{requested_username}' cannot be accessed."
                .format(requested_username=requested_username)
            )

        return requested_user

    def clean(self):
        cleaned_data = super(BlockListGetForm, self).clean()

        # add additional requested_fields that are specified as separate parameters, if they were requested
        for additional_field in [StudentViewTransformer.STUDENT_VIEW_DATA, BlockCountsTransformer.BLOCK_COUNTS]:
            if cleaned_data.get(additional_field):
                cleaned_data['requested_fields'].add(additional_field)

        usage_key = cleaned_data.get('usage_key')
        if not usage_key:
            return

        cleaned_data['user'] = self.clean_requested_user(cleaned_data, usage_key.course_key)
        return cleaned_data
