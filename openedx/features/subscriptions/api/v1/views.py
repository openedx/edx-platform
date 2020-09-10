"""
HTTP endpoints for interacting with subscriptions.
"""
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from rest_framework.authentication import SessionAuthentication
from rest_framework.generics import ListAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_oauth.authentication import OAuth2Authentication

from django.http import Http404

from lms.djangoapps.commerce.api.v1.permissions import ApiKeyOrModelPermission
from openedx.core.lib.api.mixins import PutAsCreateMixin
from openedx.features.subscriptions.models import UserSubscription
from openedx.features.subscriptions.api.v1.serializers import UserSubscriptionSerializer


class SubscriptionsListView(ListAPIView):
    """
    List subscriptions.
    """
    authentication_classes = (JwtAuthentication, OAuth2Authentication, SessionAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSubscriptionSerializer
    ordering_fields = ['created', ]
    ordering = ['-created']
    pagination_class = None

    def get_queryset(self):
        return_only_valid_subscriptions = True if self.request.query_params.get('valid') == 'true' else False
        user_id = self.request.query_params.get('user', self.request.user.id)
        if return_only_valid_subscriptions:
            return UserSubscription.get_valid_subscriptions(user_id=user_id)

        return UserSubscription.objects.filter(user_id=user_id)


class SubscriptionRetrieveUpdateView(PutAsCreateMixin, RetrieveUpdateAPIView):
    """
    Retrieve, update, or create UserSubscriptions.
    """
    authentication_classes = (JwtAuthentication, OAuth2Authentication, SessionAuthentication,)
    permission_classes = (ApiKeyOrModelPermission,)
    model = UserSubscription
    queryset = UserSubscription.objects.all()
    serializer_class = UserSubscriptionSerializer
    lookup_field = 'subscription_id'
    lookup_url_kwarg = 'subscription_id'
    ordering_fields = ['created', ]
    ordering = ['-created']

    def get_object(self, queryset=None):
        user_id = self.request.user.id
        self.kwargs['user'] = user_id
        user_subscription = UserSubscription.objects.filter(**self.kwargs).first()

        if not user_subscription:
            raise Http404

        return user_subscription
