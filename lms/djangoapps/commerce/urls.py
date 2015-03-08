"""
Defines the URL routes for this app.
"""

from django.conf.urls import patterns, url

from .views import OrdersView

urlpatterns = patterns(
    '',
    url(r'^orders/$', OrdersView.as_view(), name="orders"),
)
