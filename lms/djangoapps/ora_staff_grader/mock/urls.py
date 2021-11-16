"""
URLs for Enhanced Staff Grader (ESG) backend-for-frontend (BFF)

NOTE - This should be the same as ../urls.py
"""

from django.conf.urls import url

from lms.djangoapps.ora_staff_grader.mock.views import *


urlpatterns = []

urlpatterns += [
    url(
        'initialize', InitializeView.as_view(), name='initialize'
    ),
    url(
        'submissionStatus', FetchSubmissionStatusView.as_view(), name='fetch-submission-status'
    ),
    url(
        'submission/lock', LockView.as_view(), name='lock-submission'
    ),
    url(
        'submission', FetchSubmissionView.as_view(), name='fetch-submission'
    ),
    url(
        'updateGrade', UpdateGradeView.as_view(), name='update-grade'
    )
]
