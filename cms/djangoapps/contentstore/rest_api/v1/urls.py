""" Contenstore API v1 URLs. """

from django.urls import re_path

from openedx.core.constants import COURSE_ID_PATTERN

from . import views

app_name = 'v1'

urlpatterns = [
    re_path(
        fr'^proctored_exam_settings/{COURSE_ID_PATTERN}$',
        views.ProctoredExamSettingsView.as_view(),
        name="proctored_exam_settings"
    ),
    re_path(
        fr'^course_grading/{COURSE_ID_PATTERN}$',
        views.CourseGradingView.as_view(),
        name="course_grading"
    ),
    re_path(
        fr'^course_settings/{COURSE_ID_PATTERN}$',
        views.CourseSettingsView.as_view(),
        name="course_settings"
    ),
    re_path(
        fr'^course_details/{COURSE_ID_PATTERN}$',
        views.CourseDetailsView.as_view(),
        name="course_details"
    ),
]
