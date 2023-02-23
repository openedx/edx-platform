"""
Defines URLs for Survey Report.
"""

from django.urls import path
from .views import SurveyReportView, SurveyReportUpload

urlpatterns = [
    path(
        'generate_report',
        SurveyReportView.as_view(),
        name='openedx.generate_survey_report',
    ),
    path(
        'send_report/<int:id>',
        SurveyReportUpload.as_view(),
        name='openedx.send_survey_report',
    ),
]
