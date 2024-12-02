""" API Views for Course Optimizer. """

import json
import edx_api_doc_tools as apidocs
from django.conf import settings
from opaque_keys.edx.keys import CourseKey
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from user_tasks.conf import settings as user_tasks_settings
from user_tasks.models import UserTaskArtifact, UserTaskStatus

from cms.djangoapps.contentstore.core.course_optimizer_provider import generate_broken_links_descriptor
from cms.djangoapps.contentstore.rest_api.v0.serializers.course_optimizer import LinkCheckSerializer
from cms.djangoapps.contentstore.tasks import CourseLinkCheckTask, check_broken_links
from common.djangoapps.student.auth import has_course_author_access, has_studio_read_access
from common.djangoapps.util.json_request import JsonResponse
from common.djangoapps.util.views import ensure_valid_course_key
from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin, verify_course_exists, view_auth_classes
from xmodule.modulestore.django import modulestore  # lint-amnesty, pylint: disable=wrong-import-order


# Restricts status in the REST API to only those which the requesting user has permission to view.
#   These can be overwritten in django settings.
#   By default, these should be the UserTaskStatus statuses:
#   'Pending', 'In Progress', 'Succeeded', 'Failed', 'Canceled', 'Retrying'
STATUS_FILTERS = user_tasks_settings.USER_TASKS_STATUS_FILTERS


@view_auth_classes(is_authenticated=True)
class LinkCheckView(DeveloperErrorViewMixin, APIView):
    """
    View for queueing a celery task to scan a course for broken links.
    """
    @apidocs.schema(
        parameters=[
            apidocs.string_parameter("course_id", apidocs.ParameterLocation.PATH, description="Course ID"),
        ],
        responses={
            200: "Celery task queued.",
            401: "The requester is not authenticated.",
            403: "The requester cannot access the specified course.",
            404: "The requested course does not exist.",
        },
    )
    @verify_course_exists()
    def post(self, request: Request, course_id: str):
        """
        Queue celery task to scan a course for broken links.

        **Example Request**
            POST /api/contentstore/v0/link_check/{course_id}

        **POST Parameters**
        ...TODO finish description with examples
        ```json
        {
            "LinkCheckStatus": "Pending"
        }
        """
        course_key = CourseKey.from_string(course_id)

        if not has_studio_read_access(request.user, course_key):
            self.permission_denied(request)

        check_broken_links.delay(request.user.id, course_key_string, request.LANGUAGE_CODE)
        return JsonResponse({'LinkCheckStatus': UserTaskStatus.PENDING})


@view_auth_classes(is_authenticated=True)
class LinkCheckStatusView(DeveloperErrorViewMixin, APIView):
    """
    View for checking the status of the celery task and returning the results.
    """
    @apidocs.schema(
        parameters=[
            apidocs.string_parameter("course_id", apidocs.ParameterLocation.PATH, description="Course ID"),
        ],
        responses={
            200: "OK",
            401: "The requester is not authenticated.",
            403: "The requester cannot access the specified course.",
            404: "The requested course does not exist.",
        },
    )
    def get(self, request: Request, course_id: str):
        """
        TODO update description
        GET handler to return the status of the link_check task from UserTaskStatus.
        If no task has been started for the course, return 'Uninitiated'.
        If link_check task was successful, an output result is also returned.

        For reference, the following status are in UserTaskStatus:
            'Pending', 'In Progress' (sent to frontend as 'In-Progress'),
            'Succeeded', 'Failed', 'Canceled', 'Retrying'
        This function adds a status for when status from UserTaskStatus is None:
            'Uninitiated'

        **Example Request**
            GET /api/contentstore/v0/link_check_status/{course_id}

        **Example Response**
        ```json
        {
            "LinkCheckStatus": "Succeeded",
            "LinkCheckOutput": {
                sections: [
                {
                    id: <string>,
                    displayName: <string>,
                    subsections: [
                    {
                        id: <string>,
                        displayName: <string>,
                        units: [
                        {
                            id: <string>,
                            displayName: <string>,
                            blocks: [
                            {
                                id: <string>,
                                url: <string>,
                                brokenLinks: [
                                    <string>,
                                    <string>,
                                    <string>,
                                    ...,
                                ],
                                lockedLinks: [
                                    <string>,
                                    <string>,
                                    <string>,
                                    ...,
                                ],
                            },
                            { <another block> },
                            ],
                        },
                        { <another unit> },
                        ],
                    },
                    { <another subsection },
                    ],
                },
                { <another section> },
                ],
            },
        }
        """
        course_key = CourseKey.from_string(course_id)
        if not has_course_author_access(request.user, course_key):
            self.permission_denied(request)
        
        task_status = _latest_task_status(request, course_id)
        status = None
        broken_links_dto = None
        error = None
        if task_status is None:
            # The task hasn't been initialized yet; did we store info in the session already?
            try:
                session_status = request.session['link_check_status']
                status = session_status[course_id]
            except KeyError:
                status = 'Uninitiated'
        else:
            status = task_status.state
            if task_status.state == UserTaskStatus.SUCCEEDED:
                artifact = UserTaskArtifact.objects.get(status=task_status, name='BrokenLinks')
                with artifact.file as file:
                    content = file.read()
                    json_content = json.loads(content)
                    broken_links_dto = generate_broken_links_descriptor(json_content, request.user)
            elif task_status.state in (UserTaskStatus.FAILED, UserTaskStatus.CANCELED):
                errors = UserTaskArtifact.objects.filter(status=task_status, name='Error')
                if errors:
                    error = errors[0].text
                    try:
                        error = json.loads(error)
                    except ValueError:
                        # Wasn't JSON, just use the value as a string
                        pass

        data = {
            'LinkCheckStatus': status,
            **({'LinkCheckOutput': broken_links_dto} if broken_links_dto else {}),
            **({'LinkCheckError': error} if error else {})
        }

        serializer = LinkCheckSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        return Response(serializer.data)


def _latest_task_status(request, course_key_string, view_func=None):
    """
    Get the most recent link check status update for the specified course
    key.
    """
    args = {'course_key_string': course_key_string}
    name = CourseLinkCheckTask.generate_name(args)
    task_status = UserTaskStatus.objects.filter(name=name)
    for status_filter in STATUS_FILTERS:
        task_status = status_filter().filter_queryset(request, task_status, view_func)
    return task_status.order_by('-created').first()
