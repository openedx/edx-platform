"""
Defines the URL routes for this app.
"""

from django.conf.urls import patterns, url

from .views import OrdersView, checkout_cancel

urlpatterns = patterns(
    '',
    url(r'^orders/$', OrdersView.as_view(), name="orders"),
    url(r'^checkout/cancel/$', checkout_cancel, name="checkout_cancel"),
)
