"""
These views handle all actions in Studio related to link checking of
courses
"""


import json
import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import Http404, HttpResponse
from django.utils.translation import gettext as _
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST
from opaque_keys.edx.keys import CourseKey
from user_tasks.conf import settings as user_tasks_settings
from user_tasks.models import UserTaskArtifact, UserTaskStatus

from common.djangoapps.student.auth import has_course_author_access
from common.djangoapps.util.json_request import JsonResponse
from common.djangoapps.util.views import ensure_valid_course_key
from cms.djangoapps.contentstore.xblock_storage_handlers.view_handlers import get_xblock
from cms.djangoapps.contentstore.core.course_optimizer_provider import create_dto
from cms.djangoapps.contentstore.xblock_storage_handlers.xblock_helpers import usage_key_with_run
from xmodule.modulestore.django import modulestore  # lint-amnesty, pylint: disable=wrong-import-order

from ..tasks import CourseLinkCheckTask, check_broken_links
from ..utils import reverse_course_url

__all__ = [
    'link_check_handler',
    'link_check_status_handler',
]

log = logging.getLogger(__name__)

# Tuple containing zero or more filters for UserTaskStatus listing REST API calls.
STATUS_FILTERS = user_tasks_settings.USER_TASKS_STATUS_FILTERS


@transaction.non_atomic_requests
@require_POST
@ensure_csrf_cookie
@login_required
@ensure_valid_course_key
def link_check_handler(request, course_key_string):
    """
    POST handler to queue an asynchronous celery task. 
    This celery task checks a course for broken links.
    """
    course_key = CourseKey.from_string(course_key_string)
    if not has_course_author_access(request.user, course_key):
        raise PermissionDenied()

    course_block = modulestore().get_course(course_key)
    if course_block is None:
        raise Http404

    check_broken_links.delay(request.user.id, course_key_string, request.LANGUAGE_CODE)
    return JsonResponse({'LinkCheckStatus': UserTaskStatus.PENDING})


@transaction.non_atomic_requests
@require_GET
@ensure_csrf_cookie
@login_required
@ensure_valid_course_key
def link_check_status_handler(request, course_key_string):
    """
    GET handler to return the status of the link_check task from UserTaskStatus.
    If no task has been started for the course, return 'Uninitiated'.
    If link_check task was successful, an output result is also returned.

    For reference, the following status are in UserTaskStatus:
        'Pending', 'In Progress', 'Succeeded',
        'Failed', 'Canceled', 'Retrying'
    """
    course_key = CourseKey.from_string(course_key_string)
    if not has_course_author_access(request.user, course_key):
        raise PermissionDenied()

    # The task status record is authoritative once it's been created
    task_status = _latest_task_status(request, course_key_string, link_check_status_handler)
    status = None
    broken_links_dto = None
    error = None
    if task_status is None:
        # The task hasn't been initialized yet; did we store info in the session already?
        try:
            session_status = request.session['link_check_status']
            status = session_status[course_key_string]
        except KeyError:
            status = 'Uninitiated'
    else:
        status = task_status.state
        if task_status.state == UserTaskStatus.SUCCEEDED:
            artifact = UserTaskArtifact.objects.get(status=task_status, name='BrokenLinks')
            with artifact.file as file:
                content = file.read()
                json_content = json.loads(content)
                broken_links_dto = create_dto(json_content, request.user)
        elif task_status.state in (UserTaskStatus.FAILED, UserTaskStatus.CANCELED):
            errors = UserTaskArtifact.objects.filter(status=task_status, name='Error')
            if errors:
                error = errors[0].text
                try:
                    error = json.loads(error)
                except ValueError:
                    # Wasn't JSON, just use the value as a string
                    pass

    response = {
        'LinkCheckStatus': status,
        **({'LinkCheckOutput': broken_links_dto} if broken_links_dto else {}),
        **({'LinkCheckError': error} if error else {})
    }
    return JsonResponse(response)


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
