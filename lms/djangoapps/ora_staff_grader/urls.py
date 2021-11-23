"""
URLs for Enhanced Staff Grader (ESG) backend-for-frontend (BFF)
"""
from django.conf.urls import include, url
from django.urls.conf import path


from lms.djangoapps.ora_staff_grader.views import (
    InitializeView, SubmissionFetchView, SubmissionLockView, SubmissionStatusFetchView,
)


urlpatterns = []
app_name = "ora-staff-grader"

urlpatterns += [
    url('mock/', include('lms.djangoapps.ora_staff_grader.mock.urls')),
    path(
        'initialize/', InitializeView.as_view(), name='initialize'
    ),
    path(
        'submission/status', SubmissionStatusFetchView.as_view(), name='fetch-submission-status'
    ),
    path(
        'submission/lock', SubmissionLockView.as_view(), name='lock'
    ),
    path(
        'submission/', SubmissionFetchView.as_view(), name='fetch-submission'
    )
]
