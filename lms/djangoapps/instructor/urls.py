"""
Instructor API endpoint new urls.
"""

from django.conf import settings
from django.conf.urls import url

import lms.djangoapps.instructor.views.api as instructor_api

app_name = 'instructor'
urlpatterns = [
    url(
        r'^v1/course/{}/tasks$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        instructor_api.InstructorTasks.as_view(),
        name='list_instructor_tasks',
    ),
    url(
        r'^v1/course/{}/reports$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        instructor_api.ReportDownloadsList.as_view(),
        name='list_report_downloads',
    ),
    url(
        r'^v1/course/{}/reports/problem_responses$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        instructor_api.ProblemResponseReport.as_view(),
        name='get_problem_responses',
    ),
]
