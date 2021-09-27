"""
Urls for Admin Dashboard
"""
from django.conf.urls import url
from django.conf import settings

from openedx.features.wikimedia_features.admin_dashboard.course_reports import course_reports
from openedx.features.wikimedia_features.admin_dashboard.admin_task.api import average_calculate_grades_csv, progress_report_csv

app_name = 'admin_dashboard'
urlpatterns = [
    url(
        r'^average_calculate_grades_csv/{}$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        average_calculate_grades_csv,
        name='average_calculate_grades_csv'
    ),
    url(
        r'^progress_report_csv/{}$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        progress_report_csv,
        name='progress_report_csv'
    ),
    url(r'', course_reports, name='course_reports'),
]
