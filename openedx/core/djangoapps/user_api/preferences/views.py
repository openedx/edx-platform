"""
NOTE: this API is WIP and has not yet been approved. Do not use this API without talking to Christina or Andy.

For more information, see:
https://openedx.atlassian.net/wiki/display/TNL/User+API
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import OAuth2Authentication, SessionAuthentication
from rest_framework import permissions

from openedx.core.lib.api.parsers import MergePatchParser
from ..api.account import AccountUserNotFound, AccountNotAuthorized
from ..models import PreferenceNotFound, PreferenceUpdateError
from .api import (
    get_user_preference, get_user_preferences, set_user_preference, update_user_preferences, delete_user_preference
)


class PreferencesView(APIView):
    """
        **Use Cases**

            Get or update the user's preference information. Updates are only supported through merge patch.

        **Example Requests**:

            GET /api/user/v0/preferences/{username}/

            PATCH /api/user/v0/preferences/{username}/ with content_type "application/merge-patch+json"

        **Response Value for GET**

            A dict will be returned with key/value pairs (all of type String).

        **Response for PATCH**

             Returns a 204 status if successful, with no additional content.
             If "application/merge-patch+json" is not the specified content_type, returns a 415 status.

    """
    authentication_classes = (OAuth2Authentication, SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    parser_classes = (MergePatchParser,)

    def get(self, request, username):
        """
        GET /api/user/v0/preferences/{username}/
        """
        try:
            user_preferences = get_user_preferences(request.user, username=username)
        except (AccountUserNotFound, AccountNotAuthorized):
            return Response(status=status.HTTP_404_NOT_FOUND)

        return Response(user_preferences)

    def patch(self, request, username):
        """
        PATCH /api/user/v0/preferences/{username}/
        """
        try:
            update_user_preferences(request.user, request.DATA, username=username)
        except (AccountUserNotFound, AccountNotAuthorized):
            return Response(status=status.HTTP_404_NOT_FOUND)
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

            GET /api/user/v0/preferences/{username}/{preference_key}

            PUT /api/user/v0/preferences/{username}/{preference_key}

            DELETE /api/user/v0/preferences/{username}/{preference_key}

        **Response Values for PUT**

            TODO

        **Response for PUT**

             TODO

    """
    authentication_classes = (OAuth2Authentication, SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, username, preference_key):
        """
        GET /api/user/v0/preferences/{username}/{preference_key}
        """
        try:
            value = get_user_preference(request.user, preference_key, username=username)
        except (AccountUserNotFound, PreferenceNotFound, AccountNotAuthorized):
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(value)

    def put(self, request, username, preference_key):
        """
        PUT /api/user/v0/preferences/{username}/{preference_key}
        """
        try:
            set_user_preference(request.user, preference_key, request.DATA, username=username)
        except (AccountUserNotFound, PreferenceNotFound, AccountNotAuthorized):
            return Response(status=status.HTTP_404_NOT_FOUND)
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
        DELETE /api/user/v0/preferences/{username}/{preference_key}
        """
        try:
            delete_user_preference(request.user, preference_key, username=username)
        except (AccountUserNotFound, PreferenceNotFound, AccountNotAuthorized):
            return Response(status=status.HTTP_404_NOT_FOUND)
        except PreferenceUpdateError as error:
            return Response(
                {
                    "developer_message": error.developer_message,
                    "user_message": error.user_message
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)
