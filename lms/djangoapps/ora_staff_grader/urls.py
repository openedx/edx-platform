"""
URLs for Enhanced Staff Grader (ESG) backend-for-frontend (BFF)
"""
from django.conf.urls import include, url
from django.urls.conf import path


from lms.djangoapps.ora_staff_grader.views import (
    InitializeView, SubmissionFetchView, SubmissionLockView, SubmissionStatusFetchView, UpdateGradeView
)


urlpatterns = []
app_name = "ora-staff-grader"

urlpatterns += [
    url('mock/', include('lms.djangoapps.ora_staff_grader.mock.urls')),
    url(
         r'^initialize', InitializeView.as_view(), name='initialize'
    ),
    url(
        r'^submission/status', SubmissionStatusFetchView.as_view(), name='fetch-submission-status'
    ),
    url(
        r'^submission/lock', SubmissionLockView.as_view(), name='lock'
    ),
    url(
        r'^submission/grade', UpdateGradeView.as_view(), name='update-grade'
    ),
    url(
        r'^submission?$', SubmissionFetchView.as_view(), name='fetch-submission'
    )
]
