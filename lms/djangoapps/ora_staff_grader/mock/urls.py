"""
URLs for Enhanced Staff Grader (ESG) backend-for-frontend (BFF)

NOTE - This should be the same as ../urls.py
"""

from django.conf.urls import url

from lms.djangoapps.ora_staff_grader.mock.views import *


urlpatterns = []

urlpatterns += [
    url(
        r'^initialize', InitializeView.as_view(), name='initialize'
    ),
    url(
        r'^submission/status', SubmissionStatusFetchView.as_view(), name='fetch-submission-status'
    ),
    url(
        r'^submission/lock', SubmissionLockView.as_view(), name='lock-submission'
    ),
    url(
        r'^submission/grade', UpdateGradeView.as_view(), name='update-grade'
    ),
    url(
        r'^submission?$', SubmissionFetchView.as_view(), name='fetch-submission'
    ),
]
