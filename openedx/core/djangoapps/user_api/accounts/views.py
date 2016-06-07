"""
NOTE: this API is WIP and has not yet been approved. Do not use this API without talking to Christina or Andy.

For more information, see:
https://openedx.atlassian.net/wiki/display/TNL/User+API
"""
from django.db import transaction
from edx_rest_framework_extensions.authentication import JwtAuthentication
from rest_framework import permissions
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet

from openedx.core.lib.api.authentication import (
    SessionAuthenticationAllowInactiveUser,
    OAuth2AuthenticationAllowInactiveUser,
)
from openedx.core.lib.api.parsers import MergePatchParser
from .api import get_account_settings, update_account_settings
from ..errors import UserNotFound, UserNotAuthorized, AccountUpdateError, AccountValidationError


class AccountViewSet(ViewSet):
    """
        **Use Cases**

            Get or update a user's account information. Updates are supported
            only through merge patch.

        **Example Requests**

            GET /api/user/v1/accounts?usernames={username1,username2}[?view=shared]
            GET /api/user/v1/accounts/{username}/[?view=shared]

            PATCH /api/user/v1/accounts/{username}/{"key":"value"} "application/merge-patch+json"

        **Response Values for GET**

            If no user exists with the specified username, an HTTP 404 "Not
            Found" response is returned.

            If the user makes the request for her own account, or makes a
            request for another account and has "is_staff" access, an HTTP 200
            "OK" response is returned. The response contains the following
            values.

            * bio: null or textual representation of user biographical
              information ("about me").
            * country: An ISO 3166 country code or null.
            * date_joined: The date the account was created, in the string
              format provided by datetime. For example, "2014-08-26T17:52:11Z".
            * email: Email address for the user. New email addresses must be confirmed
              via a confirmation email, so GET does not reflect the change until
              the address has been confirmed.
            * gender: One of the following values:

                * null
                * "f"
                * "m"
                * "o"

            * goals: The textual representation of the user's goals, or null.
            * is_active: Boolean representation of whether a user is active.
            * language: The user's preferred language, or null.
            * language_proficiencies: Array of language preferences. Each
              preference is a JSON object with the following keys:

                * "code": string ISO 639-1 language code e.g. "en".

            * level_of_education: One of the following values:

                * "p": PhD or Doctorate
                * "m": Master's or professional degree
                * "b": Bachelor's degree
                * "a": Associate's degree
                * "hs": Secondary/high school
                * "jhs": Junior secondary/junior high/middle school
                * "el": Elementary/primary school
                * "none": None
                * "o": Other
                * null: The user did not enter a value

            * mailing_address: The textual representation of the user's mailing
              address, or null.
            * name: The full name of the user.
            * profile_image: A JSON representation of a user's profile image
              information. This representation has the following keys.

                * "has_image": Boolean indicating whether the user has a profile
                  image.
                * "image_url_*": Absolute URL to various sizes of a user's
                  profile image, where '*' matches a representation of the
                  corresponding image size, such as 'small', 'medium', 'large',
                  and 'full'. These are configurable via PROFILE_IMAGE_SIZES_MAP.

            * requires_parental_consent: True if the user is a minor
              requiring parental consent.
            * username: The username associated with the account.
            * year_of_birth: The year the user was born, as an integer, or null.
            * account_privacy: The user's setting for sharing her personal
              profile. Possible values are "all_users" or "private".
            * accomplishments_shared: Signals whether badges are enabled on the
              platform and should be fetched.

            For all text fields, plain text instead of HTML is supported. The
            data is stored exactly as specified. Clients must HTML escape
            rendered values to avoid script injections.

            If a user who does not have "is_staff" access requests account
            information for a different user, only a subset of these fields is
            returned. The returns fields depend on the
            ACCOUNT_VISIBILITY_CONFIGURATION configuration setting and the
            visibility preference of the user for whom data is requested.

            Note that a user can view which account fields they have shared
            with other users by requesting their own username and providing
            the "view=shared" URL parameter.

        **Response Values for PATCH**

            Users can only modify their own account information. If the
            requesting user does not have the specified username and has staff
            access, the request returns an HTTP 403 "Forbidden" response. If
            the requesting user does not have staff access, the request
            returns an HTTP 404 "Not Found" response to avoid revealing the
            existence of the account.

            If no user exists with the specified username, an HTTP 404 "Not
            Found" response is returned.

            If "application/merge-patch+json" is not the specified content
            type, a 415 "Unsupported Media Type" response is returned.

            If validation errors prevent the update, this method returns a 400
            "Bad Request" response that includes a "field_errors" field that
            lists all error messages.

            If a failure at the time of the update prevents the update, a 400
            "Bad Request" error is returned. The JSON collection contains
            specific errors.

            If the update is successful, updated user account data is returned.
    """
    authentication_classes = (
        OAuth2AuthenticationAllowInactiveUser, SessionAuthenticationAllowInactiveUser, JwtAuthentication
    )
    permission_classes = (permissions.IsAuthenticated,)
    parser_classes = (MergePatchParser,)

    def list(self, request):
        """
        GET /api/user/v1/accounts?username={username1,username2}
        """
        usernames = request.GET.get('username')
        try:
            if usernames:
                usernames = usernames.strip(',').split(',')
            account_settings = get_account_settings(
                request, usernames, view=request.query_params.get('view'))
        except UserNotFound:
            return Response(status=status.HTTP_403_FORBIDDEN if request.user.is_staff else status.HTTP_404_NOT_FOUND)

        return Response(account_settings)

    def retrieve(self, request, username):
        """
        GET /api/user/v1/accounts/{username}/
        """
        try:
            account_settings = get_account_settings(
                request, [username], view=request.query_params.get('view'))
        except UserNotFound:
            return Response(status=status.HTTP_403_FORBIDDEN if request.user.is_staff else status.HTTP_404_NOT_FOUND)

        return Response(account_settings[0])

    def partial_update(self, request, username):
        """
        PATCH /api/user/v1/accounts/{username}/

        Note that this implementation is the "merge patch" implementation proposed in
        https://tools.ietf.org/html/rfc7396. The content_type must be "application/merge-patch+json" or
        else an error response with status code 415 will be returned.
        """
        try:
            with transaction.atomic():
                update_account_settings(request.user, request.data, username=username)
                account_settings = get_account_settings(request, [username])[0]
        except UserNotAuthorized:
            return Response(status=status.HTTP_403_FORBIDDEN if request.user.is_staff else status.HTTP_404_NOT_FOUND)
        except UserNotFound:
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

        return Response(account_settings)
