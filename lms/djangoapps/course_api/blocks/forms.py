"""

"""
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.forms import Form, CharField, Field, MultipleHiddenInput
from django.http import Http404
from rest_framework.exceptions import PermissionDenied

from courseware.access import _has_access_to_course
from xmodule.modulestore.django import modulestore
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import UsageKey

from transformers.student_view import StudentViewTransformer
from transformers.block_counts import BlockCountsTransformer


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
            raise ValidationError("'{}' is not a valid depth value".format(value))

    def clean_usage_key(self):
        usage_key = self.cleaned_data['usage_key']

        try:
            usage_key = UsageKey.from_string(usage_key)
            usage_key = usage_key.replace(course_key=modulestore().fill_in_run(usage_key.course_key))
        except InvalidKeyError:
            raise ValidationError("'{}' is not a valid usage key".format(unicode(usage_key)))

        return usage_key

    def clean(self):
        cleaned_data = super(BlockListGetForm, self).clean()

        # add additional requested_fields that are specified as separate parameters, if they were requested
        for additional_field in [StudentViewTransformer.STUDENT_VIEW_DATA, BlockCountsTransformer.BLOCK_COUNTS]:
            if cleaned_data.get(additional_field):
                cleaned_data['requested_fields'].add(additional_field)

        usage_key = self.cleaned_data.get('usage_key')
        if not usage_key:
            return

        # validate and set user
        requested_username = cleaned_data.get('user', '')
        requesting_user = self.initial['request'].user

        if requesting_user.username.lower() == requested_username.lower():
            cleaned_data['user'] = requesting_user
        else:
            # the requesting user is trying to access another user's view
            # verify requesting user is staff and update requested user's object
            if not _has_access_to_course(requesting_user, 'staff', usage_key.course_key):
                raise PermissionDenied(
                    "'{requesting_username}' does not have permission to access view for '{requested_username}'."
                    .format(requesting_username=requesting_user.username, requested_username=requested_username)
                )

            # get requested user object
            try:
                cleaned_data['user'] = User.objects.get(username=requested_username)
            except (User.DoesNotExist):
                raise Http404("'{username}' does not exist.".format(username=requested_username))

        return cleaned_data
