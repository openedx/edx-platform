""" Verification API URLs. """
from django.conf.urls import patterns, url, include

urlpatterns = patterns(
    '',
    url(r'^v0/', include('verify_student.verification_api.v0.urls', namespace='v0')),
)
