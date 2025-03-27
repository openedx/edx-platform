"""
URLs for course_dates API
"""

from django.conf import settings
from django.urls import re_path

from .views import AllCourseDatesAPIView

urlpatterns = [
    re_path(rf"^{settings.USERNAME_PATTERN}", AllCourseDatesAPIView.as_view(), name="all-course-dates"),
]
