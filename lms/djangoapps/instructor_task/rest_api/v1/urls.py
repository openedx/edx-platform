"""
Instructor Task Django app REST API URLs.
"""
from django.conf import settings
from django.urls import re_path

from lms.djangoapps.instructor_task.rest_api.v1.views import (
    ListScheduledBulkEmailInstructorTasks,
    DeleteScheduledBulkEmailInstructorTask
)


urlpatterns = [
    re_path(
        fr"schedules/{settings.COURSE_ID_PATTERN}/bulk_email/$",
        ListScheduledBulkEmailInstructorTasks.as_view(),
        name="get-scheduled-bulk-email-messages"
    ),
    re_path(
        fr"schedules/{settings.COURSE_ID_PATTERN}/bulk_email/(?P<schedule_id>[0-9]+)$",
        DeleteScheduledBulkEmailInstructorTask.as_view(),
        name="delete-scheduled-bulk-email-messages"
    )
]
