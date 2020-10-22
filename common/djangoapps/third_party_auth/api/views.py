"""
Third Party Auth REST API views
"""

from collections import namedtuple

from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import Http404
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from rest_framework import exceptions, status, throttling
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_oauth.authentication import OAuth2Authentication
from social_django.models import UserSocialAuth

from openedx.core.lib.api.authentication import OAuth2AuthenticationAllowInactiveUser
from openedx.core.lib.api.permissions import ApiKeyHeaderPermission
from third_party_auth import pipeline
from third_party_auth.api import serializers
from third_party_auth.api.permissions import ThirdPartyAuthProviderApiPermission
from third_party_auth.provider import Registry


class ProviderBaseThrottle(throttling.UserRateThrottle):
    """
    Base throttle for provider queries
    """

    def allow_request(self, request, view):
        """
        Only throttle unprivileged requests.
        """
        if view.is_unprivileged_query(request, view.get_identifier_for_requested_user(request)):
            return super(ProviderBaseThrottle, self).allow_request(request, view)
        return True


class ProviderBurstThrottle(ProviderBaseThrottle):
    """
    Maximum number of provider requests in a quick burst.
    """
    rate = settings.TPA_PROVIDER_BURST_THROTTLE  # Default '10/min'


class ProviderSustainedThrottle(ProviderBaseThrottle):
    """
    Maximum number of provider requests over time.
    """
    rate = settings.TPA_PROVIDER_SUSTAINED_THROTTLE  # Default '50/day'


class BaseUserView(APIView):
    """
    Common core of UserView and UserViewV2
    """
    identifier = namedtuple('identifier', ['kind', 'value'])
    identifier_kinds = ['email', 'username']

    authentication_classes = (
        # Users may want to view/edit the providers used for authentication before they've
        # activated their account, so we allow inactive users.
        OAuth2AuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )
    throttle_classes = [ProviderSustainedThrottle, ProviderBurstThrottle]

    def do_get(self, request, identifier):
        """
        Fulfill the request, now that the identifier has been specified.
        """
        is_unprivileged = self.is_unprivileged_query(request, identifier)

        if is_unprivileged:
            if not getattr(settings, 'ALLOW_UNPRIVILEGED_SSO_PROVIDER_QUERY', False):
                return Response(status=status.HTTP_403_FORBIDDEN)
        try:
            user = User.objects.get(**{identifier.kind: identifier.value})
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        providers = pipeline.get_provider_user_states(user)

        active_providers = [
            self.get_provider_data(assoc, is_unprivileged)
            for assoc in providers if assoc.has_account
        ]

        # In the future this can be trivially modified to return the inactive/disconnected providers as well.

        return Response({
            "active": active_providers
        })

    def get_provider_data(self, assoc, is_unprivileged):
        """
        Return the data for the specified provider.

        If the request is unprivileged, do not return the remote ID of the user.
        """
        provider_data = {
            "provider_id": assoc.provider.provider_id,
            "name": assoc.provider.name,
        }
        if not is_unprivileged:
            provider_data["remote_id"] = assoc.remote_id
        return provider_data

    def is_unprivileged_query(self, request, identifier):
        """
        Return True if a non-superuser requests information about another user.

        Params must be a dict that includes only one of 'username' or 'email'
        """
        if identifier.kind not in self.identifier_kinds:
            # This is already checked before we get here, so raise a 500 error
            # if the check fails.
            raise ValueError("Identifier kind {} not in {}".format(identifier.kind, self.identifier_kinds))

        self_request = False
        if identifier == self.identifier('username', request.user.username):
            self_request = True
        elif identifier.kind == 'email' and getattr(identifier, 'value', object()) == request.user.email:
            # AnonymousUser does not have an email attribute, so fall back to
            # something that will never compare equal to the provided email.
            self_request = True
        if self_request:
            # We can always ask for our own provider
            return False
        # We are querying permissions for a user other than the current user.
        if not request.user.is_superuser and not ApiKeyHeaderPermission().has_permission(request, self):
            # The user does not have elevated permissions.
            return True
        return False


class UserView(BaseUserView):
    """
    List the third party auth accounts linked to the specified user account.

    [DEPRECATED]

    This view uses heuristics to guess whether the provided identifier is a
    username or email address.  Instead, use /api/third_party_auth/v0/users/
    and specify ?username=foo or ?email=foo@exmaple.com.

    **Example Request**

        GET /api/third_party_auth/v0/users/{username}
        GET /api/third_party_auth/v0/users/{email@example.com}

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

    def get(self, request, username):
        """Read provider information for a user.

        Allows reading the list of providers for a specified user.

        Args:
            request (Request): The HTTP GET request
            username (str): Fetch the list of providers linked to this user

        Return:
            JSON serialized list of the providers linked to this user.

        """
        identifier = self.get_identifier_for_requested_user(request)
        return self.do_get(request, identifier)

    def get_identifier_for_requested_user(self, _request):
        """
        Return an identifier namedtuple for the requested user.
        """
        if u'@' in self.kwargs[u'username']:
            id_kind = u'email'
        else:
            id_kind = u'username'
        return self.identifier(id_kind, self.kwargs[u'username'])


# TODO: When removing deprecated UserView, rename this view to UserView.
class UserViewV2(BaseUserView):
    """
    List the third party auth accounts linked to the specified user account.

    **Example Request**

        GET /api/third_party_auth/v0/users/?username={username}
        GET /api/third_party_auth/v0/users/?email={email@example.com}

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

    def get(self, request):
        """
        Read provider information for a user.

        Allows reading the list of providers for a specified user.

        Args:
            request (Request): The HTTP GET request

        Request Parameters:
            Must provide one of 'email' or 'username'.  If both are provided,
            the username will be ignored.

        Return:
            JSON serialized list of the providers linked to this user.

        """
        identifier = self.get_identifier_for_requested_user(request)
        return self.do_get(request, identifier)

    def get_identifier_for_requested_user(self, request):
        """
        Return an identifier namedtuple for the requested user.
        """
        identifier = None
        for id_kind in self.identifier_kinds:
            if id_kind in request.GET:
                identifier = self.identifier(id_kind, request.GET[id_kind])
                break
        if identifier is None:
            raise exceptions.ValidationError(u"Must provide one of {}".format(self.identifier_kinds))
        return identifier


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
        if uid != 'uid':
            # if yes, we add a filter for the slug on uid column
            query_set = query_set.filter(uid__startswith=uid[:-3])

        query = Q()

        usernames = self.request.query_params.getlist('username', None)
        remote_ids = self.request.query_params.getlist('remote_id', None)

        if usernames:
            usernames = ','.join(usernames)
            usernames = set(usernames.split(',')) if usernames else set()
            if usernames:
                query = query | Q(user__username__in=usernames)

        if remote_ids:
            remote_ids = ','.join(remote_ids)
            remote_ids = set(remote_ids.split(',')) if remote_ids else set()
            if remote_ids:
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
