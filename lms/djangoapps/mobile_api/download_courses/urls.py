"""
URLs for download courses API
"""

from django.conf import settings
from django.urls import re_path

from .views import DownloadCoursesAPIView


urlpatterns = [
    re_path(fr"^{settings.USERNAME_PATTERN}", DownloadCoursesAPIView.as_view(), name="download-courses"),
]
