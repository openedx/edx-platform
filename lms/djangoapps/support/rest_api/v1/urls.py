"""
URL definitions for the course_modes v1 API.
"""

from django.urls import re_path

from .views import CourseTeamManageAPIView

app_name = "v1"

urlpatterns = [
    re_path(
        r"manage_course_team/?$",
        CourseTeamManageAPIView.as_view(),
        name="manage_course_team",
    ),
]
