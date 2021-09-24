"""
URLs for Enhanced Staff Grader (ESG) backend-for-frontend (BFF)

NOTE - This should be the same as ../urls.py
"""

from django.conf.urls import url

from lms.djangoapps.ora_staff_grader.mock.views import InitializeView


urlpatterns = []

urlpatterns += [
    url(
        'initialize', InitializeView.as_view(), name='initialize'
    ),
]