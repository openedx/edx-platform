"""
URLs for mobile API
"""


from django.conf.urls import include

from .users.views import my_user_info
from django.urls import path

urlpatterns = [
    path('users/', include('lms.djangoapps.mobile_api.users.urls')),
    path('my_user_info', my_user_info, name='user-info'),
    path('course_info/', include('lms.djangoapps.mobile_api.course_info.urls')),
]
