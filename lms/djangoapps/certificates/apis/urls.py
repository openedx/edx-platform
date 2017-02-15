""" Certificates API URLs. """
from django.conf.urls import (
    include,
    patterns,
    url,
)

urlpatterns = patterns(
    '',
    url(r'^v0/', include('lms.djangoapps.certificates.apis.v0.urls', namespace='v0')),
)
