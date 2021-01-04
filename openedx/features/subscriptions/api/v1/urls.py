from django.conf.urls import include, url

from openedx.features.subscriptions.api.v1.views import (
    SubscriptionsListView,
    SubscriptionRetrieveUpdateView,
)

app_name = 'subscriptions_api'

SUBSCRIPTION_URLS = ([
    url(r'^$', SubscriptionsListView.as_view(), name='list'),
    url(r'^(?P<subscription_id>.*)/$', SubscriptionRetrieveUpdateView.as_view(), name='retrieve-update'),
], 'subscriptions')

urlpatterns = [
    url(
        '^v1/user_subscriptions/',
        include(
            SUBSCRIPTION_URLS,
            namespace='v1'
        )
    )
]
