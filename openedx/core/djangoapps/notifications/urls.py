"""
URLs for the notifications API.
"""
from django.urls import path
from django.urls import re_path
from django.conf import settings
from rest_framework import routers
from .views import CourseEnrollmentListView, UserNotificationPreferenceView

router = routers.DefaultRouter()


urlpatterns = [
    path('enrollments/', CourseEnrollmentListView.as_view(), name='enrollment-list'),
    re_path(
        fr'^configurations/{settings.COURSE_KEY_PATTERN}$',
        UserNotificationPreferenceView.as_view(),
        name='notification-preferences'
    ),
]

urlpatterns += router.urls
