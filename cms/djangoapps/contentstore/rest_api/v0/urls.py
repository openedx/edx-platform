""" Contenstore API v0 URLs. """

from django.urls import re_path

from openedx.core.constants import COURSE_ID_PATTERN
from .views import AdvancedCourseSettingsView, CourseTabSettingsView, CourseTabListView, CourseTabReorderView

app_name = "v0"

urlpatterns = [
    re_path(
        fr"^advanced_settings/{COURSE_ID_PATTERN}$",
        AdvancedCourseSettingsView.as_view(),
        name="course_advanced_settings",
    ),
    re_path(
        fr"^tabs/{COURSE_ID_PATTERN}$",
        CourseTabListView.as_view(),
        name="course_tab_list",
    ),
    re_path(
        fr"^tabs/{COURSE_ID_PATTERN}/settings$",
        CourseTabSettingsView.as_view(),
        name="course_tab_settings",
    ),
    re_path(
        fr"^tabs/{COURSE_ID_PATTERN}/reorder$",
        CourseTabReorderView.as_view(),
        name="course_tab_reorder",
    ),
]
