from django.conf.urls import url
from lms.djangoapps.philu_notifications.views import my_all_notifications

urlpatterns = [
    url(r'^view_all_notifications$', my_all_notifications, name='my_all_notifications'),
]
