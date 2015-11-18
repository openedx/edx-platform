"""
URLs for the student support app.
"""
from django.conf.urls import patterns, url

from support import views

urlpatterns = patterns(
    '',
    url(r'^$', views.index, name="index"),
    url(r'^certificates/?$', views.CertificatesSupportView.as_view(), name="certificates"),
    url(r'^refund/?$', views.RefundSupportView.as_view(), name="refund"),
)
