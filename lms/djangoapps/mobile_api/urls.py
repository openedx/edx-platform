"""
URLs for mobile API
"""


from django.urls import include, path

from .users.views import my_user_info

urlpatterns = [
    path('users/', include('lms.djangoapps.mobile_api.users.urls')),
    path('my_user_info', my_user_info, name='user-info'),
<<<<<<< HEAD
=======
    path('notifications/', include('lms.djangoapps.mobile_api.notifications.urls')),
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
    path('course_info/', include('lms.djangoapps.mobile_api.course_info.urls')),
]
