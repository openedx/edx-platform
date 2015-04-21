"""
Defines the URL routes for this app.
"""

from django.conf.urls import patterns, url

from .views import BasketsView, checkout_cancel

urlpatterns = patterns(
    '',
    url(r'^baskets/$', BasketsView.as_view(), name="baskets"),
    url(r'^checkout/cancel/$', checkout_cancel, name="checkout_cancel"),
    # (XCOM-214) For backwards compatibility with js clients during intial release
    url(r'^orders/$', BasketsView.as_view(), name="orders"),
)
