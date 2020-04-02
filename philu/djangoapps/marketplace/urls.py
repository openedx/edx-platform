from django.conf.urls import url

from philu.djangoapps.marketplace.views import (MarketplaceListingView, MarketplaceCreateRequestView,
                                                MarketplaceRequestDetailView)

urlpatterns = [
    url(
        r'^marketplaces/$',
        MarketplaceListingView.as_view(),
        name='marketplace-listing'
    ),
    url(
        r'^marketplace/request/$',
        MarketplaceCreateRequestView.as_view(),
        name='marketplace-make-request'
    ),
    url(
        r'^marketplace/(?P<pk>[0-9]+)/$',
        MarketplaceRequestDetailView.as_view(),
        name='idea-details'
    ),
]
