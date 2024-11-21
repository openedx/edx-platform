"""
URLs for the offline_mode feature.
"""
from django.urls import path

from .views import SudioCoursePublishedEventHandler

urlpatterns = [
    path('handle_course_published', SudioCoursePublishedEventHandler.as_view(), name='handle_course_published'),
]
