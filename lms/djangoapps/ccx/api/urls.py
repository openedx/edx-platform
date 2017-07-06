""" CCX API URLs. """
from django.conf.urls import patterns, url, include

urlpatterns = patterns(
    '',
    url(r'^v0/', include('lms.djangoapps.ccx.api.v0.urls', namespace='v0')),
)
