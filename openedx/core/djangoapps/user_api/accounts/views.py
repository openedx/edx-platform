"""
NOTE: this API is WIP and has not yet been approved. Do not use this API without talking to Christina or Andy.

For more information, see:
https://openedx.atlassian.net/wiki/display/TNL/User+API
"""
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import OAuth2Authentication, SessionAuthentication
from rest_framework import permissions
from rest_framework import parsers

from student.models import UserProfile
from openedx.core.djangoapps.user_api.accounts.serializers import AccountLegacyProfileSerializer, AccountUserSerializer
from openedx.core.lib.api.permissions import IsUserInUrlOrStaff
from openedx.core.lib.api.parsers import MergePatchParser


class AccountView(APIView):
    """
        **Use Cases**

            Get or update the user's account information. Updates are only supported through merge patch.

        **Example Requests**:

            GET /api/user/v0/accounts/{username}/

            PATCH /api/user/v0/accounts/{username}/ with content_type "application/merge-patch+json"

        **Response Values for GET**

            * username: username associated with the account (not editable)

            * name: full name of the user (not editable through this API)

            * email: email for the user (not editable through this API)

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
        existing_user, existing_user_profile = self._get_user_and_profile(username)
        user_serializer = AccountUserSerializer(existing_user)
        legacy_profile_serializer = AccountLegacyProfileSerializer(existing_user_profile)

        return Response(dict(user_serializer.data, **legacy_profile_serializer.data))

    def patch(self, request, username):
        """
        PATCH /api/user/v0/accounts/{username}/

        Note that this implementation is the "merge patch" implementation proposed in
        https://tools.ietf.org/html/rfc7396. The content_type must be "application/merge-patch+json" or
        else an error response with status code 415 will be returned.
        """
        existing_user, existing_user_profile = self._get_user_and_profile(username)

        # Check for fields that are not editable. Marking them read-only causes them to be ignored, but we wish to 400.
        update = request.DATA
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
            response_data = {"field_errors": field_errors}
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

        user_serializer = AccountUserSerializer(existing_user, data=update)
        legacy_profile_serializer = AccountLegacyProfileSerializer(existing_user_profile, data=update)

        for serializer in user_serializer, legacy_profile_serializer:
            validation_errors = self._get_validation_errors(update, serializer)
            if validation_errors:
                return Response(validation_errors, status=status.HTTP_400_BAD_REQUEST)
            serializer.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    def _get_user_and_profile(self, username):
        """
        Helper method to return the legacy user and profile objects based on username.
        """
        try:
            existing_user = User.objects.get(username=username)
        except ObjectDoesNotExist:
            return Response({}, status=status.HTTP_404_NOT_FOUND)
        existing_user_profile = UserProfile.objects.get(user=existing_user)

        return existing_user, existing_user_profile

    def _get_validation_errors(self, update, serializer):
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