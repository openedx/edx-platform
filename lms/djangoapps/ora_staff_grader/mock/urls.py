"""
URLs for Enhanced Staff Grader (ESG) backend-for-frontend (BFF)

NOTE - This should be the same as ../urls.py
"""

from django.conf.urls import url

from lms.djangoapps.ora_staff_grader.mock.views import *


urlpatterns = []

urlpatterns += [
    url(
        'initialize/', InitializeView.as_view(), name='initialize'
    ),
    url(
        'submission/status/', FetchSubmissionStatusView.as_view(), name='fetch-submission-status'
    ),
    url(
        'submission/lock/', LockView.as_view(), name='lock-submission'
    ),
    url(
        'submission/grade/', UpdateGradeView.as_view(), name='update-grade'
    ),
    url(
        'submission/', FetchSubmissionView.as_view(), name='fetch-submission'
    ),
]
