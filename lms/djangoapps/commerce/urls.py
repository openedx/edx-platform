"""
Defines the URL routes for this app.
"""
from django.conf.urls import patterns, url

from commerce import views


urlpatterns = patterns(
    '',
    url(r'^checkout/cancel/$', views.checkout_cancel, name='checkout_cancel'),
    url(r'^checkout/error/$', views.checkout_error, name='checkout_error'),
    url(r'^checkout/receipt/$', views.checkout_receipt, name='checkout_receipt'),
)
