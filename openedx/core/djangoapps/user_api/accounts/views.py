"""
NOTE: this API is WIP and has not yet been approved. Do not use this API without talking to Christina or Andy.

For more information, see:
https://openedx.atlassian.net/wiki/display/TNL/User+API
"""
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from util.authentication import SessionAuthenticationAllowInactiveUser, OAuth2AuthenticationAllowInactiveUser
from rest_framework import permissions

from ..errors import UserNotFound, UserNotAuthorized, AccountUpdateError, AccountValidationError
from openedx.core.lib.api.parsers import MergePatchParser
from .api import get_account_settings, update_account_settings


class AccountView(APIView):
    """
        **Use Cases**

            Get or update the user's account information. Updates are only supported through merge patch.

        **Example Requests**:

            GET /api/user/v0/accounts/{username}/[?view=shared]

            PATCH /api/user/v0/accounts/{username}/ with content_type "application/merge-patch+json"

        **Response Values for GET**

            If the user making the request has username "username", or has "is_staff" access, the following
            fields will be returned:

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

            If a user without "is_staff" access has requested account information for a different user,
            only a subset of these fields will be returned. The actual fields returned depend on the configuration
            setting ACCOUNT_VISIBILITY_CONFIGURATION, and the visibility preference of the user with username
            "username".

            Note that a user can view which account fields they have shared with other users by requesting their
            own username and providing the url parameter "view=shared".

            This method will return a 404 if no user exists with username "username".

        **Response for PATCH**

            Users can only modify their own account information. If the requesting user does not have username
            "username", this method will return with a status of 404.

            This method will also return a 404 if no user exists with username "username".

            If "application/merge-patch+json" is not the specified content_type, this method returns a 415 status.

            If the update could not be completed due to validation errors, this method returns a 400 with all
            field-specific error messages in the "field_errors" field of the returned JSON.

            If the update could not be completed due to failure at the time of update, this method returns a 400 with
            specific errors in the returned JSON.

            If the update is successful, a 204 status is returned with no additional content.
    """
    authentication_classes = (OAuth2AuthenticationAllowInactiveUser, SessionAuthenticationAllowInactiveUser)
    permission_classes = (permissions.IsAuthenticated,)
    parser_classes = (MergePatchParser,)

    def get(self, request, username):
        """
        GET /api/user/v0/accounts/{username}/
        """
        try:
            account_settings = get_account_settings(request.user, username, view=request.QUERY_PARAMS.get('view'))
        except UserNotFound:
            return Response(status=status.HTTP_404_NOT_FOUND)

        return Response(account_settings)

    def patch(self, request, username):
        """
        PATCH /api/user/v0/accounts/{username}/

        Note that this implementation is the "merge patch" implementation proposed in
        https://tools.ietf.org/html/rfc7396. The content_type must be "application/merge-patch+json" or
        else an error response with status code 415 will be returned.
        """
        try:
            with transaction.commit_on_success():
                update_account_settings(request.user, request.DATA, username=username)
        except (UserNotFound, UserNotAuthorized):
            return Response(status=status.HTTP_404_NOT_FOUND)
        except AccountValidationError as err:
            return Response({"field_errors": err.field_errors}, status=status.HTTP_400_BAD_REQUEST)
        except AccountUpdateError as err:
            return Response(
                {
                    "developer_message": err.developer_message,
                    "user_message": err.user_message
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(status=status.HTTP_204_NO_CONTENT)
