"""
Third Party Auth REST API views
"""
from django.contrib.auth.models import User
from openedx.core.lib.api.authentication import (
    OAuth2AuthenticationAllowInactiveUser,
    SessionAuthenticationAllowInactiveUser,
)
from openedx.core.lib.api.permissions import (
    ApiKeyHeaderPermission,
)
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from third_party_auth import pipeline


class UserView(APIView):
    """
    List the third party auth accounts linked to the specified user account.

    **Example Request**

        GET /api/third_party_auth/v0/users/{username}

    **Response Values**

        If the request for information about the user is successful, an HTTP 200 "OK" response
        is returned.

        The HTTP 200 response has the following values.

        * active: A list of all the third party auth providers currently linked
          to the given user's account. Each object in this list has the
          following attributes:

            * provider_id: The unique identifier of this provider (string)
            * name: The name of this provider (string)
            * remote_id: The ID of the user according to the provider. This ID
              is what is used to link the user to their edX account during
              login.
    """
    authentication_classes = (
        # Users may want to view/edit the providers used for authentication before they've
        # activated their account, so we allow inactive users.
        OAuth2AuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )

    def get(self, request, username):
        """Create, read, or update enrollment information for a user.

        HTTP Endpoint for all CRUD operations for a user course enrollment. Allows creation, reading, and
        updates of the current enrollment for a particular course.

        Args:
            request (Request): The HTTP GET request
            username (str): Fetch the list of providers linked to this user

        Return:
            JSON serialized list of the providers linked to this user.

        """
        if request.user.username != username:
            # We are querying permissions for a user other than the current user.
            if not request.user.is_superuser and not ApiKeyHeaderPermission().has_permission(request, self):
                # Return a 403 (Unauthorized) without validating 'username', so that we
                # do not let users probe the existence of other user accounts.
                return Response(status=status.HTTP_403_FORBIDDEN)

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        providers = pipeline.get_provider_user_states(user)

        active_providers = [
            {
                "provider_id": assoc.provider.provider_id,
                "name": assoc.provider.name,
                "remote_id": assoc.remote_id,
            }
            for assoc in providers if assoc.has_account
        ]

        # In the future this can be trivially modified to return the inactive/disconnected providers as well.

        return Response({
            "active": active_providers
        })
