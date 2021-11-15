"""
URLs for Enhanced Staff Grader (ESG) backend-for-frontend (BFF)
"""

from django.urls.conf import path

from lms.djangoapps.ora_staff_grader.views import InitializeView, SubmissionFetchView


urlpatterns = []

urlpatterns += [
    path(
        'initialize', InitializeView.as_view(), name='initialize'
    ),
    path(
        'submission', SubmissionFetchView.as_view(), name='fetch-submission'
    )
]
