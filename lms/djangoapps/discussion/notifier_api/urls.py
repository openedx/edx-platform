"""
URLs for the notifier api app
"""


from django.conf.urls import include, url
from rest_framework import routers

from lms.djangoapps.discussion.notifier_api.views import NotifierUsersViewSet

notifier_api_router = routers.DefaultRouter()
notifier_api_router.register(r'users', NotifierUsersViewSet, basename="notifier_users")

urlpatterns = [
    url(r'^v1/', include(notifier_api_router.urls)),
]
