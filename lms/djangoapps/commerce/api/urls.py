""" API URLs. """
from django.conf.urls import patterns, url, include

urlpatterns = patterns(
    '',
    url(r'^v0/', include('commerce.api.v0.urls', namespace='v0')),
    url(r'^v1/', include('commerce.api.v1.urls', namespace='v1')),
)
