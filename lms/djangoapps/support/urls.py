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
    url(r'^enrollment/?$', views.EnrollmentSupportView.as_view(), name="enrollment"),
    url(
        r'^enrollment/(?P<username_or_email>[\w.@+-]+)?$',
        views.EnrollmentSupportListView.as_view(),
        name="enrollment_list"
    ),
    url(r'^programs/certify/$', views.IssueProgramCertificatesView.as_view(), name='programs-certify'),
)
