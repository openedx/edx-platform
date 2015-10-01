""" API URLs. """
from django.conf.urls import patterns, url, include

urlpatterns = patterns(
    '',
    url(r'^v1/', include('enrollment.api.v1.urls', namespace='v1')),
    url(r'^v2/', include('enrollment.api.v2.urls', namespace='v2')),
)
