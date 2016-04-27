"""
Third Party Auth REST API views
"""
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import Http404
from rest_framework.generics import ListAPIView
from rest_framework_oauth.authentication import OAuth2Authentication
from social.apps.django_app.default.models import UserSocialAuth
from openedx.core.lib.api.authentication import (
    OAuth2AuthenticationAllowInactiveUser,
    SessionAuthenticationAllowInactiveUser,
)
from openedx.core.lib.api.permissions import (
    ApiKeyHeaderPermission,
)
from rest_framework import status, exceptions
from rest_framework.response import Response
from rest_framework.views import APIView
from third_party_auth import pipeline
from third_party_auth.api import serializers
from third_party_auth.api.permissions import ThirdPartyAuthProviderApiPermission
from third_party_auth.provider import Registry


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


class UserMappingView(ListAPIView):
    """
    Map between the third party auth account IDs (remote_id) and EdX username.

    This API is intended to be a server-to-server endpoint. An on-campus middleware or system should consume this.

    **Use Case**

        Get a paginated list of mappings between edX users and remote user IDs for all users currently
        linked to the given backend.

        The list can be filtered by edx username or third party ids. The filter is limited by the max length of URL.
        It is suggested to query no more than 50 usernames or remote_ids in each request to stay within above
        limitation

        The page size can be changed by specifying `page_size` parameter in the request.

    **Example Requests**

          GET /api/third_party_auth/v0/providers/{provider_id}/users

          GET /api/third_party_auth/v0/providers/{provider_id}/users?username={username1},{username2}

          GET /api/third_party_auth/v0/providers/{provider_id}/users?username={username1}&usernames={username2}

          GET /api/third_party_auth/v0/providers/{provider_id}/users?remote_id={remote_id1},{remote_id2}

          GET /api/third_party_auth/v0/providers/{provider_id}/users?remote_id={remote_id1}&remote_id={remote_id2}

          GET /api/third_party_auth/v0/providers/{provider_id}/users?username={username1}&remote_id={remote_id1}

    **URL Parameters**

        * provider_id: The unique identifier of third_party_auth provider (e.g. "saml-ubc", "oa2-google", etc.
          This is not the same thing as the backend_name.). (Optional/future: We may also want to allow
          this to be an 'external domain' like 'ssl:MIT' so that this API can also search the legacy
          ExternalAuthMap table used by Standford/MIT)

    **Query Parameters**

        * remote_ids: Optional. List of comma separated remote (third party) user IDs to filter the result set.
          e.g. ?remote_ids=8721384623

        * usernames: Optional. List of comma separated edX usernames to filter the result set.
          e.g. ?usernames=bob123,jane456

        * page, page_size: Optional. Used for paging the result set, especially when getting
          an unfiltered list.

    **Response Values**

        If the request for information about the user is successful, an HTTP 200 "OK" response
        is returned.

        The HTTP 200 response has the following values:

        * count: The number of mappings for the backend.

        * next: The URI to the next page of the mappings.

        * previous: The URI to the previous page of the mappings.

        * num_pages: The number of pages listing the mappings.

        * results:  A list of mappings returned. Each collection in the list
          contains these fields.

            * username: The edx username

            * remote_id: The Id from third party auth provider
    """
    authentication_classes = (
        OAuth2Authentication,
    )

    serializer_class = serializers.UserMappingSerializer
    provider = None

    def get_queryset(self):
        provider_id = self.kwargs.get('provider_id')

        # permission checking. We allow both API_KEY access and OAuth2 client credential access
        if not (
                self.request.user.is_superuser or ApiKeyHeaderPermission().has_permission(self.request, self) or
                ThirdPartyAuthProviderApiPermission(provider_id).has_permission(self.request, self)
        ):
            raise exceptions.PermissionDenied()

        # provider existence checking
        self.provider = Registry.get(provider_id)
        if not self.provider:
            raise Http404

        query_set = UserSocialAuth.objects.select_related('user').filter(provider=self.provider.backend_name)

        # build our query filters
        # When using multi-IdP backend, we only retrieve the ones that are for current IdP.
        # test if the current provider has a slug
        uid = self.provider.get_social_auth_uid('uid')
        if uid is not 'uid':
            # if yes, we add a filter for the slug on uid column
            query_set = query_set.filter(uid__startswith=uid[:-3])

        query = Q()

        usernames = self.request.QUERY_PARAMS.getlist('username', None)
        remote_ids = self.request.QUERY_PARAMS.getlist('remote_id', None)

        if usernames:
            usernames = ','.join(usernames)
            usernames = set(usernames.split(',')) if usernames else set()
            if len(usernames):
                query = query | Q(user__username__in=usernames)

        if remote_ids:
            remote_ids = ','.join(remote_ids)
            remote_ids = set(remote_ids.split(',')) if remote_ids else set()
            if len(remote_ids):
                query = query | Q(uid__in=[self.provider.get_social_auth_uid(remote_id) for remote_id in remote_ids])

        return query_set.filter(query)

    def get_serializer_context(self):
        """
        Extra context provided to the serializer class with current provider. We need the provider to
        remove idp_slug from the remote_id if there is any
        """
        context = super(UserMappingView, self).get_serializer_context()
        context['provider'] = self.provider

        return context
