"""
NOTE: this API is WIP and has not yet been approved. Do not use this API without talking to Christina or Andy.

For more information, see:
https://openedx.atlassian.net/wiki/display/TNL/User+API
"""
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _
import datetime
from pytz import UTC

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import OAuth2Authentication, SessionAuthentication
from rest_framework import permissions

from openedx.core.djangoapps.user_api.accounts.serializers import AccountLegacyProfileSerializer, AccountUserSerializer
from openedx.core.djangoapps.user_api.api.account import AccountUserNotFound, AccountUpdateError
from openedx.core.lib.api.parsers import MergePatchParser
from openedx.core.lib.api.permissions import IsUserInUrlOrStaff
from student.models import UserProfile
from student.views import do_email_change_request


class AccountView(APIView):
    """
        **Use Cases**

            Get or update the user's account information. Updates are only supported through merge patch.

        **Example Requests**:

            GET /api/user/v0/accounts/{username}/

            PATCH /api/user/v0/accounts/{username}/ with content_type "application/merge-patch+json"

        **Response Values for GET**

            * username: username associated with the account (not editable)

            * name: full name of the user (must be at least two characters)

            * email: email for the user (the new email address must be confirmed via a confirmation email, so GET will
                not reflect the change until the address has been confirmed)

            * date_joined: date this account was created (not editable), in the string format provided by
                datetime (for example, "2014-08-26T17:52:11Z")

            * gender: null (not set), "m", "f", or "o"

            * year_of_birth: null or integer year

            * level_of_education: null (not set), or one of the following choices:

                * "p" signifying "Doctorate"
                * "m" signifying "Master's or professional degree"
                * "b" signifying "Bachelor's degree"
                * "a" signifying "Associate's degree"
                * "hs" signifying "Secondary/high school"
                * "jhs" signifying "Junior secondary/junior high/middle school"
                * "el" signifying "Elementary/primary school"
                * "none" signifying "None"
                * "o" signifying "Other"

             * language: null or name of preferred language

             * country: null (not set), or a Country corresponding to one of the ISO 3166-1 countries

             * mailing_address: null or textual representation of mailing address

             * goals: null or textual representation of goals

        **Response for PATCH**

             Returns a 204 status if successful, with no additional content.
             If "application/merge-patch+json" is not the specified content_type, returns a 415 status.

    """
    authentication_classes = (OAuth2Authentication, SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated, IsUserInUrlOrStaff)
    parser_classes = (MergePatchParser,)

    def get(self, request, username):
        """
        GET /api/user/v0/accounts/{username}/
        """
        try:
            account_settings = AccountView.get_serialized_account(username)
        except AccountUserNotFound:
            return Response(status=status.HTTP_404_NOT_FOUND)

        return Response(account_settings)

    @staticmethod
    def get_serialized_account(username):
        """Returns the user's account information serialized as JSON.

        Note:
          This method does not perform authentication so it is up to the caller
          to ensure that only the user themselves or staff can access the account.

        Args:
          username (str): The username for the desired account.

        Returns:
           A dict containing each of the account's fields.

        Raises:
           AccountUserNotFound: raised if there is no account for the specified username.
        """
        existing_user, existing_user_profile = AccountView._get_user_and_profile(username)
        user_serializer = AccountUserSerializer(existing_user)
        legacy_profile_serializer = AccountLegacyProfileSerializer(existing_user_profile)

        return dict(user_serializer.data, **legacy_profile_serializer.data)

    def patch(self, request, username):
        """
        PATCH /api/user/v0/accounts/{username}/

        Note that this implementation is the "merge patch" implementation proposed in
        https://tools.ietf.org/html/rfc7396. The content_type must be "application/merge-patch+json" or
        else an error response with status code 415 will be returned.
        """
        # Disallow users with is_staff access from calling patch on any account.
        if request.user.username != username:
            return Response(status=status.HTTP_404_NOT_FOUND)

        try:
            AccountView.update_account(username, request.DATA)
        except AccountUserNotFound:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except AccountUpdateError as err:
            return Response(err.error_info, status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_204_NO_CONTENT)

    @staticmethod
    def update_account(username, update):
        """Update the account for the given username.

        Note:
            No authorization or permissions checks are done in this method. It is up to the caller
            of this method to enforce the contract that this method is only called
            by the user with the specified username.

        Arguments:
            username (string): the username associated with the account to change
            update (dict): the updated account field values

        Raises:
            AccountUserNotFound: no user exists with the specified username
            AccountUpdateError: the update could not be completed, usually due to validation errors
                (for example, read-only fields were specified or field values are not legal)
        """
        existing_user, existing_user_profile = AccountView._get_user_and_profile(username)

        # If user has requested to change email, we must call the multi-step process to handle this.
        # It is not handled by the serializer (which considers email to be read-only).
        new_email = None
        if "email" in update:
            new_email = update["email"]
            del update["email"]

        # If user has requested to change name, store old name because we must update associated metadata
        # after the save process is complete.
        old_name = None
        if "name" in update:
            old_name = existing_user_profile.name

        # Check for fields that are not editable. Marking them read-only causes them to be ignored, but we wish to 400.
        read_only_fields = set(update.keys()).intersection(
            AccountUserSerializer.Meta.read_only_fields + AccountLegacyProfileSerializer.Meta.read_only_fields
        )
        if read_only_fields:
            field_errors = {}
            for read_only_field in read_only_fields:
                field_errors[read_only_field] = {
                    "developer_message": "This field is not editable via this API",
                    "user_message": _("Field '{field_name}' cannot be edited.".format(field_name=read_only_field))
                }
            raise AccountUpdateError({"field_errors": field_errors})

        # If the user asked to change email, send the request now.
        if new_email:
            try:
                do_email_change_request(existing_user, new_email)
            except ValueError as err:
                response_data = {
                    "developer_message": "Error thrown from do_email_change_request: '{}'".format(err.message),
                    "user_message": err.message
                }
                raise AccountUpdateError(response_data)

        user_serializer = AccountUserSerializer(existing_user, data=update)
        legacy_profile_serializer = AccountLegacyProfileSerializer(existing_user_profile, data=update)

        for serializer in user_serializer, legacy_profile_serializer:
            validation_errors = AccountView._get_validation_errors(update, serializer)
            if validation_errors:
                raise AccountUpdateError(validation_errors)
            serializer.save()

        # If the name was changed, store information about the change operation.
        if old_name:
            meta = existing_user_profile.get_meta()
            if 'old_names' not in meta:
                meta['old_names'] = []
            meta['old_names'].append([
                old_name,
                "Name change requested through account API",
                datetime.datetime.now(UTC).isoformat()
            ])
            existing_user_profile.set_meta(meta)
            existing_user_profile.save()

    @staticmethod
    def _get_user_and_profile(username):
        """
        Helper method to return the legacy user and profile objects based on username.
        """
        try:
            existing_user = User.objects.get(username=username)
            existing_user_profile = UserProfile.objects.get(user=existing_user)
        except ObjectDoesNotExist:
            raise AccountUserNotFound()

        return existing_user, existing_user_profile

    @staticmethod
    def _get_validation_errors(update, serializer):
        """
        Helper method that returns any validation errors that are present.
        """
        validation_errors = {}
        if not serializer.is_valid():
            field_errors = {}
            errors = serializer.errors
            for key, value in errors.iteritems():
                if isinstance(value, list) and len(value) > 0:
                    developer_message = value[0]
                else:
                    developer_message = "Invalid value: {field_value}'".format(field_value=update[key])
                field_errors[key] = {
                    "developer_message": developer_message,
                    "user_message": _("Value '{field_value}' is not valid for field '{field_name}'.".format(
                        field_value=update[key], field_name=key)
                    )
                }

            validation_errors['field_errors'] = field_errors
        return validation_errors
