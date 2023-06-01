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
        fr'^proctoring_errors/{COURSE_ID_PATTERN}$',
        views.ProctoringErrorsView.as_view(),
        name="proctoring_errors"
    ),
]
