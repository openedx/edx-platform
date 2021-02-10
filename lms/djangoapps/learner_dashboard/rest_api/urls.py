"""
URLs file for the Program Learner Dashboard API.
"""

from django.conf.urls import include, url

app_name = 'learner_dashboard'

urlpatterns = [
    url(r'^v1/', include('lms.djangoapps.learner_dashboard.rest_api.v1.urls')),
]
