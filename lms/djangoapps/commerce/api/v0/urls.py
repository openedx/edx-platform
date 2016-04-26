""" API v0 URLs. """
from django.conf.urls import patterns, url, include

from commerce.api.v0 import views


BASKET_URLS = patterns(
    '',
    url(r'^$', views.BasketsView.as_view(), name='create'),
    url(r'^(?P<basket_id>[\w]+)/order/$', views.BasketOrderView.as_view(), name='retrieve_order'),
)

urlpatterns = patterns(
    '',
    url(r'^baskets/', include(BASKET_URLS, namespace='baskets')),
)
