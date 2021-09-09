"""
Urls for Admin Dashboard
"""
from django.conf.urls import url

from openedx.features.wikimedia_features.admin_dashboard.course_reports import course_reports


app_name = 'admin_dashboard'

urlpatterns = [
    url(r'', course_reports, name='course_reports'),
]
