"""
Instructor Task Django app REST API views.
"""
import logging

from celery.states import REVOKED
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response
from rest_framework import generics, status

from lms.djangoapps.instructor_task.data import InstructorTaskTypes
from lms.djangoapps.instructor_task.models import InstructorTaskSchedule, SCHEDULED
from lms.djangoapps.instructor_task.rest_api.v1.serializers import ScheduledBulkEmailSerializer
from lms.djangoapps.instructor_task.rest_api.v1.permissions import CanViewOrDeleteScheduledBulkCourseEmails

log = logging.getLogger(__name__)


class ListScheduledBulkEmailInstructorTasks(generics.ListAPIView):
    """
    Read only view to list all scheduled bulk email messages for a course-run.

    Path: GET `api/instructor_task/v1/schedules/{course_id}/bulk_email`

    Returns:
        * 200: OK - Contains a list of all scheduled bulk email instructor tasks that haven't been executed yet. This
               data also includes information about the and course email instance associated with each task.
        * 403: User does not have the required role to view this data.
    """
    authentication_classes = (
        JwtAuthentication,
        SessionAuthentication,
    )
    permission_classes = (
        CanViewOrDeleteScheduledBulkCourseEmails,
    )
    serializer_class = ScheduledBulkEmailSerializer

    def get_queryset(self):
        """
        Filters the results so that only scheduled bulk email tasks for the specific course-run are returned.
        """
        course_id = self.kwargs["course_id"]
        return (
            InstructorTaskSchedule.objects
            .filter(task__course_id=course_id)
            .filter(task__task_state=SCHEDULED)
            .filter(task__task_type=InstructorTaskTypes.BULK_COURSE_EMAIL)
        )


class DeleteScheduledBulkEmailInstructorTask(generics.DestroyAPIView):
    """
    A view that deletes an instructor task schedule instance and revokes the associated instructor task.

    Path: DELETE `api/instructor_task/v1/schedules/{course_id}/bulk_email/{task_schedule_id}`

    Returns:
        * 204: No Content - Deleting the schedule was successful.
        * 404: Requested schedule object could not be found and thus could not be deleted.
    """
    authentication_classes = (
        JwtAuthentication,
        SessionAuthentication,
    )
    permission_classes = (
        CanViewOrDeleteScheduledBulkCourseEmails,
    )

    def destroy(self, request, *args, **kwargs):
        course_id = kwargs["course_id"]
        schedule_id = kwargs["schedule_id"]

        log.info(f"Cancelling instructor task schedule with id '{schedule_id}' in course '{course_id}'")
        try:
            schedule = InstructorTaskSchedule.objects.get(id=schedule_id)
        except InstructorTaskSchedule.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        # update the task's status to REVOKED and then delete the task schedule instance
        task = schedule.task
        log.info(f"Revoking instructor task with id '{task.id}' for course '{task.course_id}'")
        task.task_state = REVOKED
        task.save()
        schedule.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
