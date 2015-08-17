""" API URLs. """
from django.conf.urls import patterns, url, include

urlpatterns = patterns(
    '',
    url(r'^v1/', include('commerce.api.v1.urls', namespace='v1')),
)
