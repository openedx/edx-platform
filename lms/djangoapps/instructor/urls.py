"""
Instructor API endpoint new urls.
"""

from django.conf import settings
from django.conf.urls import url

import lms.djangoapps.instructor.views.api


urlpatterns = [
    url(
        r'^v1/course/{}/tasks$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        lms.djangoapps.instructor.views.api.InstructorTasks.as_view(),
        name='list_instructor_tasks',
    ),
    url(
        r'^v1/course/{}/reports$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        lms.djangoapps.instructor.views.api.ReportDownloadsList.as_view(),
        name='list_report_downloads',
    ),
    url(
        r'^v1/course/{}/reports/problem_responses$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        lms.djangoapps.instructor.views.api.ProblemResponseReport.as_view(),
        name='get_problem_responses',
    ),
]

if settings.FEATURES.get('ENABLE_INSTRUCTOR_BACKGROUND_TASKS'):
    urlpatterns += [
        url(
            r'^v1/tasks$',
            'lms.djangoapps.instructor_task.views.instructor_task_status',
            name='get_instructor_task_status',
        ),
    ]
