from django.conf.urls import url

from openedx.features.marketplace.views import (MarketplaceListView, MarketplaceCreateRequestView,
                                                MarketplaceRequestDetailView)

urlpatterns = [
    url(
        r'^$',
        MarketplaceListView.as_view(),
        name='marketplace-listing'
    ),
    url(
        r'^request/$',
        MarketplaceCreateRequestView.as_view(),
        name='marketplace-make-request'
    ),
    url(
        r'^(?P<pk>[0-9]+)/$',
        MarketplaceRequestDetailView.as_view(),
        name='marketplace-details'
    ),
]
