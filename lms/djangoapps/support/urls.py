"""
URLs for the student support app.
"""
from django.conf.urls import patterns, url

from support import views

from lms.djangoapps.support.views.contact_us import ContactUsView

urlpatterns = patterns(
    '',
    url(r'^$', views.index, name="index"),
    url(r'^certificates/?$', views.CertificatesSupportView.as_view(), name="certificates"),
    url(r'^refund/?$', views.RefundSupportView.as_view(), name="refund"),
    url(r'^enrollment/?$', views.EnrollmentSupportView.as_view(), name="enrollment"),
    url(r'^contact_us/?$', ContactUsView.as_view(), name="contact_us"),
    url(
        r'^enrollment/(?P<username_or_email>[\w.@+-]+)?$',
        views.EnrollmentSupportListView.as_view(),
        name="enrollment_list"
    ),
)
