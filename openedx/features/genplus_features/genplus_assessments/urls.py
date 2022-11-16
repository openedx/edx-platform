"""
URLs for genplus learning app.
"""
from django.conf.urls import url, include
from .views import AssessmentReportPDFView


app_name = 'genplus_assessments'

urlpatterns = (
    url(r'^download-report/$', AssessmentReportPDFView.as_view()),
    url(
        r'^api/v1/',
        include(
            'openedx.features.genplus_features.genplus_assessments.api.v1.urls',
            namespace='genplus_assessments_api_v1'
        )
    ),
)
