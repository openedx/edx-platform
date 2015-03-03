"""
NOTE: this API is WIP and has not yet been approved. Do not use this API without talking to Christina or Andy.

For more information, see:
https://openedx.atlassian.net/wiki/display/TNL/User+API
"""
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import OAuth2Authentication, SessionAuthentication
from rest_framework import permissions

from ..serializers import UserSerializer
from openedx.core.djangoapps.user_api.api.account import AccountNotAuthorized
from openedx.core.lib.api.permissions import IsUserInUrlOrStaff
from openedx.core.lib.api.parsers import MergePatchParser


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
    permission_classes = (permissions.IsAuthenticated, IsUserInUrlOrStaff)
    parser_classes = (MergePatchParser,)

    def get(self, request, username):
        """
        GET /api/user/v0/preferences/{username}/
        """
        try:
            existing_user = User.objects.get(username=username)
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        user_serializer = UserSerializer(existing_user)
        return Response(user_serializer.data["preferences"])

    def patch(self, request, username):
        """
        PATCH /api/user/v0/preferences/{username}/
        """
        for preference_key in request.DATA.keys():
            preference_value = request.data[preference_key]
            if preference_value:
                user_preference, __ = existing_user.preferences.get_or_create(user=existing_user, key=preference_key)
                user_preference.value = request.DATA
                user_preference.save()
            else



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
    permission_classes = (permissions.IsAuthenticated, IsUserInUrlOrStaff)

    def get(self, request, username, preference_key):
        """
        GET /api/user/v0/preferences/{username}/{preference_key}
        """
        try:
            existing_user = User.objects.get(username=username)
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        try:
            preference_value = existing_user.preferences.get(key=preference_key).value
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        return Response(preference_value)

    def put(self, request, username, preference_key):
        """
        PUT /api/user/v0/preferences/{username}/{preference_key}
        """
        try:
            existing_user = User.objects.get(username=username)
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if not isinstance(request.DATA, basestring):
            return Response({}, status.HTTP_400_BAD_REQUEST)

        user_preference, __ = existing_user.preferences.get_or_create(user=existing_user, key=preference_key)
        user_preference.value = request.DATA
        user_preference.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    def delete(self, request, username, preference_key):
        """
        DELETE /api/user/v0/preferences/{username}/{preference_key}
        """
        if request.user.username != username:
            raise Response(status=status.HTTP_404_NOT_FOUND)

        try:
            self._delete_preference(request.user, preference_key)
        except ObjectDoesNotExist:
            raise Response(status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @staticmethod
    def _delete_preference(requesting_user, preference_key, username=None):
        """
        """
        if username is None:
            username = requesting_user.username

        if requesting_user.username != username:
            raise AccountNotAuthorized()

        user_preference = requesting_user.preferences.get(key=preference_key)
        user_preference.delete()
