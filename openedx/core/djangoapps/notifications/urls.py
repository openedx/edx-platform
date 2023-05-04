"""
URLs for the notifications API.
"""
from django.urls import path
from rest_framework import routers

from .views import CourseEnrollmentListView

router = routers.DefaultRouter()

urlpatterns = [
    path('enrollments/', CourseEnrollmentListView.as_view(), name='enrollment-list'),
]

urlpatterns += router.urls
