""" Contenstore API v1 URLs. """

from django.urls import re_path

from openedx.core.constants import COURSE_ID_PATTERN

from . import views

app_name = 'v1'

urlpatterns = [
    re_path(
        r'^proctored_exam_settings/{}$'.format(COURSE_ID_PATTERN),
        views.ProctoredExamSettingsView.as_view(),
        name="proctored_exam_settings"
    ),
]
