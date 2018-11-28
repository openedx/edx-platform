"""
URLs for mobile API
"""

from django.conf.urls import include, url

from .users.views import my_user_info

urlpatterns = [
    url(r'^users/', include('mobile_api.users.urls')),
    url(r'^my_user_info', my_user_info, name='user-info'),
    url(r'^video_outlines/', include('mobile_api.video_outlines.urls')),
    url(r'^course_info/', include('mobile_api.course_info.urls')),
]
