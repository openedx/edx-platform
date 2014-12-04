# pylint: disable=C0103
from django.conf.urls import include, patterns, url

urlpatterns = patterns(
    '',
    url(r'^courses/', include('server_api.courses.urls', namespace='courses')),
)
