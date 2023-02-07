""" Contenstore API v1 URLs. """

from django.urls import re_path
from django.conf import settings

from openedx.core.constants import COURSE_ID_PATTERN

from .views import proctored_exam_settings, xblock

app_name = 'v1'

urlpatterns = [
    re_path(
        fr'^proctored_exam_settings/{COURSE_ID_PATTERN}$',
        proctored_exam_settings.ProctoredExamSettingsView.as_view(),
        name="proctored_exam_settings"
    ),
    re_path(fr'^xblock/{settings.COURSE_ID_PATTERN}/{settings.USAGE_KEY_PATTERN}?$',
            xblock.XblockView.as_view(), name='xblock'),
]
