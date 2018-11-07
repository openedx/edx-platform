"""
Defines the URL routes for this app.
"""
from django.conf.urls import url

from . import views

app_name = 'commerce'
urlpatterns = [
    url(r'^checkout/cancel/$', views.checkout_cancel, name='checkout_cancel'),
    url(r'^checkout/error/$', views.checkout_error, name='checkout_error'),
    url(r'^checkout/receipt/$', views.checkout_receipt, name='checkout_receipt'),
    url(r'^checkout/verification_status/$', views.user_verification_status, name='user_verification_status'),
]
