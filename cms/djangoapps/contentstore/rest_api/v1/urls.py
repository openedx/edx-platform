""" Contenstore API v1 URLs. """

from django.conf.urls import url

from . import views
from openedx.core.constants import COURSE_ID_PATTERN

app_name = 'v1'

urlpatterns = [
    url(
        r'^proctored_exam_settings/{course_id}/$'.format(course_id=COURSE_ID_PATTERN),
        views.ProctoredExamSettingsView.as_view(),
        name="proctored_exam_settings"
    ),
]
