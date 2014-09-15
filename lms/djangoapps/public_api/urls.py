from django.conf.urls import patterns, url, include
from rest_framework import routers

from users.views import my_user_info

# Additionally, we include login URLs for the browseable API.
urlpatterns = patterns('',
    url(r'^users/', include('public_api.users.urls')),
    url(r'^my_user_info', my_user_info),
    url(r'^video_outlines/', include('public_api.video_outlines.urls')),
    url(r'^course_info/', include('public_api.course_info.urls')),
)
