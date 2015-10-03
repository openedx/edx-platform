""" Verification API v0 URLs. """
from django.conf.urls import patterns, url

from lms.djangoapps.verify_student.verification_api.v0 import views

urlpatterns = patterns(
    '',
    url(
        r'^users/(?P<username>[^/]+)/photo_verification_status/$',
        views.PhotoVerificationStatusView.as_view(),
        name='photo_verification_status',
    ),
)
