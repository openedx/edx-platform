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

            Get or update a user's account information. Updates are supported only through merge patch.

        **Example Requests**:

            GET /api/user/v0/accounts/{username}/[?view=shared]

            PATCH /api/user/v0/accounts/{username}/{"key":"value"} "application/merge-patch+json"

        **Response Values for GET**

            If the user makes the request for her own account, or makes a
            request for another account and has "is_staff" access, the response
            contains:

                * username: The username associated with the account.

                * name: The full name of the user.

                * email: The confirmed email address for the user. The request
                  will not return an unconfirmed email address.

                * date_joined: The date the account was created, in
                  the string format provided by datetime (for example,
                  "2014-08-26T17:52:11Z").

                * gender: One of the fullowing values:

                  * "m" 
                  * "f"
                  * "o"
                  * null

                * year_of_birth: The year the user was born, as an integer, or
                  null.

                * level_of_education: One of the following values:

                    * "p": PhD or Doctorate
                    * "m": Master's or professional degree
                    * "b": Bachelor's degree
                    * "a": Associate's degree
                    * "hs": Secondary/high school
                    * "jhs": Junior secondary/junior high/middle school
                    * "el": Elementary/primary school
                    * "none": "None"
                    * "o": "Other"
                    * null: The user did not enter a value.

                * language: The user's preferred language, or null.

                * country: A ISO 3166 country code or null.

                * mailing_address: The textual representation of the user's
                  mailing address, or null.

                * goals: The textual representation of the user's goals, or null.

            If a user who does not have "is_staff" access requests account
            information for a different user, only a subset of these fields is
            returned. The fields returned depend on the configuration setting
            ACCOUNT_VISIBILITY_CONFIGURATION, and the visibility preference of
            the user for whom data is requested.

            Note that a user can view which account fields they have shared with
            other users by requesting their own username and providing the url
            parameter "view=shared".

            If no user exists with the specified username, a 404 error is
            returned.

        **Response Values for PATCH**

            Users can modify only their own account information. If the user
            attempts to modify another user's account, a 404 error is returned.

            If no user exists with the specified username, a 404 error is
            returned.

            If "application/merge-patch+json" is not the specified content type,
            a 415 error is returned.

            If the update could not be completed due to validation errors, this
            method returns a 400 error with all error messages in the
            "field_errors" field of the returned JSON.

            If the update could not be completed due to a failure at the time of
            the update, a 400 error is returned with specific errors in the
            returned JSON collection.

            If the update is successful, a 204 status is returned with no
            additional content.
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
