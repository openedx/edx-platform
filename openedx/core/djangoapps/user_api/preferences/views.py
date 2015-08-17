"""
NOTE: this API is WIP and has not yet been approved. Do not use this API without talking to Christina or Andy.

For more information, see:
https://openedx.atlassian.net/wiki/display/TNL/User+API
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import permissions

from django.db import transaction
from django.utils.translation import ugettext as _

from openedx.core.lib.api.authentication import (
    SessionAuthenticationAllowInactiveUser,
    OAuth2AuthenticationAllowInactiveUser,
)
from openedx.core.lib.api.parsers import MergePatchParser
from openedx.core.lib.api.permissions import IsUserInUrlOrStaff
from ..errors import UserNotFound, UserNotAuthorized, PreferenceValidationError, PreferenceUpdateError
from .api import (
    get_user_preference, get_user_preferences, set_user_preference, update_user_preferences, delete_user_preference
)


class PreferencesView(APIView):
    """
        **Use Cases**

            Get or update the user's preference information. Updates are only supported through merge patch.
            Preference values of null in a patch request are treated as requests to remove the preference.

        **Example Requests**:

            GET /api/user/v1/preferences/{username}/

            PATCH /api/user/v1/preferences/{username}/ with content_type "application/merge-patch+json"

        **Response Value for GET**

            If the user makes the request for her own account, or makes a
            request for another account and has "is_staff" access, the response
            contains a JSON dictionary with a key/value pair (of type String)
            for each preference.

            The list of preferences depends on your implementation. By default,
            preferences include:

            * pref-lan: The user's preferred language, as set in account
              settings.

            * account_privacy: The user's setting for sharing her personal
              profile. Possible values are ``all_users`` or ``private``.

            If a user without "is_staff" access requests preferences for a
            different user, a 404 error is returned.

            If the specified username does not exist, a 404 is returned.

        **Response for PATCH**

            Users can only modify their own preferences. If the requesting user
            does not have username "username", this method will return with a
            status of 403 for users with staff access but a 404 for ordinary
            users to avoid leaking the existence of the account.

            This method will also return a 404 if no user exists with username
            "username".

            If "application/merge-patch+json" is not the specified content_type,
            this method returns a 415 status.

            If the update could not be completed due to validation errors, this
            method returns a 400 with all preference-specific error messages in
            the "field_errors" field of the returned JSON.

            If the update could not be completed due to failure at the time of
            update, this method returns a 400 with specific errors in the
            returned JSON.

            If the update is successful, a 204 status is returned with no
            additional content.

    """
    authentication_classes = (OAuth2AuthenticationAllowInactiveUser, SessionAuthenticationAllowInactiveUser)
    permission_classes = (permissions.IsAuthenticated, IsUserInUrlOrStaff)
    parser_classes = (MergePatchParser,)

    def get(self, request, username):
        """
        GET /api/user/v1/preferences/{username}/
        """
        try:
            user_preferences = get_user_preferences(request.user, username=username)
        except UserNotAuthorized:
            return Response(status=status.HTTP_403_FORBIDDEN)
        except UserNotFound:
            return Response(status=status.HTTP_404_NOT_FOUND)

        return Response(user_preferences)

    def patch(self, request, username):
        """
        PATCH /api/user/v1/preferences/{username}/
        """
        if not request.DATA or not getattr(request.DATA, "keys", None):
            error_message = _("No data provided for user preference update")
            return Response(
                {
                    "developer_message": error_message,
                    "user_message": error_message
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            with transaction.commit_on_success():
                update_user_preferences(request.user, request.DATA, username=username)
        except UserNotAuthorized:
            return Response(status=status.HTTP_403_FORBIDDEN)
        except UserNotFound:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except PreferenceValidationError as error:
            return Response(
                {"field_errors": error.preference_errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        except PreferenceUpdateError as error:
            return Response(
                {
                    "developer_message": error.developer_message,
                    "user_message": error.user_message
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class PreferencesDetailView(APIView):
    """
        **Use Cases**

            Get, create, update, or delete a specific user preference.

        **Example Requests**:

            GET /api/user/v1/preferences/{username}/{preference_key}

            PUT /api/user/v1/preferences/{username}/{preference_key}

            DELETE /api/user/v1/preferences/{username}/{preference_key}

        **Response Values for GET**

            The preference value will be returned as a JSON string.

            If a user without "is_staff" access has requested preferences for a
            different user, this method returns a 404.

            If the specified username or preference does not exist, this method
            returns a 404.

        **Response Values for PUT**

            A successful put returns a 204 and no content.

            Users can only modify their own preferences. If the requesting user
            does not have username "username", this method will return with a
            status of 403 for users with staff access but a 404 for ordinary
            users to avoid leaking the existence of the account.

            If the specified preference does not exist, this method returns a
            404.

        **Response for DELETE**

            A successful delete returns a 204 and no content.

            Users can only delete their own preferences. If the requesting user
            does not have username "username", this method will return with a
            status of 403 for users with staff access but a 404 for ordinary
            users to avoid leaking the existence of the account.

            If the specified preference does not exist, this method returns a
            404.

    """
    authentication_classes = (OAuth2AuthenticationAllowInactiveUser, SessionAuthenticationAllowInactiveUser)
    permission_classes = (permissions.IsAuthenticated, IsUserInUrlOrStaff)

    def get(self, request, username, preference_key):
        """
        GET /api/user/v1/preferences/{username}/{preference_key}
        """
        try:
            value = get_user_preference(request.user, preference_key, username=username)
            # There was no preference with that key, raise a 404.
            if value is None:
                return Response(status=status.HTTP_404_NOT_FOUND)
        except UserNotAuthorized:
            return Response(status=status.HTTP_403_FORBIDDEN)
        except UserNotFound:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(value)

    def put(self, request, username, preference_key):
        """
        PUT /api/user/v1/preferences/{username}/{preference_key}
        """
        try:
            set_user_preference(request.user, preference_key, request.DATA, username=username)
        except UserNotAuthorized:
            return Response(status=status.HTTP_403_FORBIDDEN)
        except UserNotFound:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except PreferenceValidationError as error:
            return Response(
                {
                    "developer_message": error.preference_errors[preference_key]["developer_message"],
                    "user_message": error.preference_errors[preference_key]["user_message"]
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except PreferenceUpdateError as error:
            return Response(
                {
                    "developer_message": error.developer_message,
                    "user_message": error.user_message
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    def delete(self, request, username, preference_key):
        """
        DELETE /api/user/v1/preferences/{username}/{preference_key}
        """
        try:
            preference_existed = delete_user_preference(request.user, preference_key, username=username)
        except UserNotAuthorized:
            return Response(status=status.HTTP_403_FORBIDDEN)
        except UserNotFound:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except PreferenceUpdateError as error:
            return Response(
                {
                    "developer_message": error.developer_message,
                    "user_message": error.user_message
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if not preference_existed:
            return Response(status=status.HTTP_404_NOT_FOUND)

        return Response(status=status.HTTP_204_NO_CONTENT)
