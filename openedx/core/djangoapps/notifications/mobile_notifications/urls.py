"""
URLs for the mobile notifications API.
"""
from django.urls import path
from rest_framework import routers

from .views import (
    UserNotificationPreferenceView,
)

router = routers.DefaultRouter()

urlpatterns = [
    path('configurations/', UserNotificationPreferenceView.as_view(), name='user-configurations-list'),
]

urlpatterns += router.urls
