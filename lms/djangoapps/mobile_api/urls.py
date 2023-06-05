"""
URLs for mobile API
"""


from django.conf.urls import include, url

from .users.views import my_user_info

urlpatterns = [
    url(r'^users/', include('lms.djangoapps.mobile_api.users.urls')),
    url(r'^my_user_info', my_user_info, name='user-info'),
    url(r'^course_info/', include('lms.djangoapps.mobile_api.course_info.urls')),
]
