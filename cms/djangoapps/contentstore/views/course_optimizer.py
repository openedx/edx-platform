"""
These views handle all actions in Studio related to link checking of
courses
"""


import base64
import json
import logging
import os
import re
import shutil
from wsgiref.util import FileWrapper

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.files import File
from django.core.files.storage import FileSystemStorage
from django.db import transaction
from django.http import Http404, HttpResponse, HttpResponseNotFound, StreamingHttpResponse
from django.shortcuts import redirect
from django.utils.translation import gettext as _
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_http_methods
from edx_django_utils.monitoring import set_custom_attribute, set_custom_attributes_for_course_key
from opaque_keys.edx.keys import CourseKey
from path import Path as path
from storages.backends.s3boto3 import S3Boto3Storage
from user_tasks.conf import settings as user_tasks_settings
from user_tasks.models import UserTaskArtifact, UserTaskStatus

from common.djangoapps.edxmako.shortcuts import render_to_response
from common.djangoapps.student.auth import has_course_author_access
from common.djangoapps.util.json_request import JsonResponse
from common.djangoapps.util.monitoring import monitor_import_failure
from common.djangoapps.util.views import ensure_valid_course_key
from xmodule.modulestore.django import modulestore  # lint-amnesty, pylint: disable=wrong-import-order

from ..storage import course_import_export_storage
from ..tasks import CourseLinkCheckTask, check_broken_links
from ..utils import reverse_course_url

__all__ = [
    'link_check_handler', 'link_check_output_handler', 'link_check_status_handler',
]

log = logging.getLogger(__name__)

STATUS_FILTERS = user_tasks_settings.USER_TASKS_STATUS_FILTERS


def send_tarball(tarball, size):
    """
    Renders a tarball to response, for use when sending a tar.gz file to the user.
    """
    wrapper = FileWrapper(tarball, settings.COURSE_EXPORT_DOWNLOAD_CHUNK_SIZE)
    response = StreamingHttpResponse(wrapper, content_type='application/x-tgz')
    response['Content-Disposition'] = 'attachment; filename=%s' % os.path.basename(tarball.name)
    response['Content-Length'] = size
    return response


@transaction.non_atomic_requests
@ensure_csrf_cookie
@login_required
@require_http_methods(('GET', 'POST'))
@ensure_valid_course_key
def link_check_handler(request, course_key_string):
    """
    The restful handler for checking broken links in a course.

    GET
        html: return html page for import page ???
        json: not supported ???
    POST
        Start a Celery task to check broken links in the course

    The Studio UI uses a POST request to start the export asynchronously, with
    a link appearing on the page once it's ready.
    """
    course_key = CourseKey.from_string(course_key_string)
    if not has_course_author_access(request.user, course_key):
        raise PermissionDenied()
    courselike_block = modulestore().get_course(course_key)
    if courselike_block is None:
        raise Http404
    context = {
        'context_course': courselike_block,
        'courselike_home_url': reverse_course_url("course_handler", course_key),
    }
    context['status_url'] = reverse_course_url('export_status_handler', course_key)

    # an _accept URL parameter will be preferred over HTTP_ACCEPT in the header.
    requested_format = request.GET.get('_accept', request.META.get('HTTP_ACCEPT', 'text/html'))

    if request.method == 'POST':
        check_broken_links.delay(request.user.id, course_key_string)
        return JsonResponse({'ExportStatus': 1})
    else:
        # Only HTML request format is supported (no JSON).
        return HttpResponse(status=406)


@transaction.non_atomic_requests
@require_GET
@ensure_csrf_cookie
@login_required
@ensure_valid_course_key
def link_check_status_handler(request, course_key_string):
    """
    Returns an integer corresponding to the status of a link check. These are:

        -X : Link check unsuccessful due to some error with X as stage [0-3]
        0 : No status info found (export done or task not yet created)
        1 : Checking links
        2 : Saving???
        3 : Link check successful

    If the link check was successful, a result is also returned.
    """
    course_key = CourseKey.from_string(course_key_string)
    if not has_course_author_access(request.user, course_key):
        raise PermissionDenied()

    # The task status record is authoritative once it's been created
    task_status = _latest_task_status(request, course_key_string, link_check_status_handler)
    output_url = None
    error = None
    if task_status is None:
        # The task hasn't been initialized yet; did we store info in the session already?
        try:
            session_status = request.session["link_check_status"]
            status = session_status[course_key_string]
        except KeyError:
            status = 0
    elif task_status.state == UserTaskStatus.SUCCEEDED:
        # TODO WRITE THE OUTPUT HERE
        status = 3
        artifact = UserTaskArtifact.objects.get(status=task_status, name='Output')
        if isinstance(artifact.file.storage, FileSystemStorage):
            output_url = reverse_course_url('export_output_handler', course_key)
        elif isinstance(artifact.file.storage, S3Boto3Storage):
            filename = os.path.basename(artifact.file.name)
            disposition = f'attachment; filename="{filename}"'
            output_url = artifact.file.storage.url(artifact.file.name, parameters={
                'ResponseContentDisposition': disposition,
                'ResponseContentType': 'application/json'
            })
        else:
            output_url = artifact.file.storage.url(artifact.file.name)
        output_json = f'raytest'
        # TODO WRITE THE OUTPUT HERE
    elif task_status.state in (UserTaskStatus.FAILED, UserTaskStatus.CANCELED):
        status = max(-(task_status.completed_steps + 1), -2)
        errors = UserTaskArtifact.objects.filter(status=task_status, name='Error')
        if errors:
            error = errors[0].text
            try:
                error = json.loads(error)
            except ValueError:
                # Wasn't JSON, just use the value as a string
                pass
    else:
        status = min(task_status.completed_steps + 1, 2)

    response = {"LinkCheckStatus": status}
    if output_json:
        response['LinkCheckOutput'] = output_json
    elif error:
        response['LinkCheckError'] = error
    return JsonResponse(response)


@transaction.non_atomic_requests
@require_GET
@ensure_csrf_cookie
@login_required
@ensure_valid_course_key
def link_check_output_handler(request, course_key_string):
    """
    Returns the response body produced by a link scan.  Only used in
    environments such as devstack where the output is stored in a local
    filesystem instead of an external service like S3.
    """
    course_key = CourseKey.from_string(course_key_string)
    if not has_course_author_access(request.user, course_key):
        raise PermissionDenied()

    task_status = _latest_task_status(request, course_key_string, link_check_output_handler)
    if task_status and task_status.state == UserTaskStatus.SUCCEEDED:
        artifact = None
        try:
            artifact = UserTaskArtifact.objects.get(status=task_status, name='Output')
            tarball = course_import_export_storage.open(artifact.file.name)
            data = {
              'something': 123,
            }
            return JsonResponse(data)
        except UserTaskArtifact.DoesNotExist:
            raise Http404  # lint-amnesty, pylint: disable=raise-missing-from
        finally:
            if artifact:
                artifact.file.close()
    else:
        raise Http404


def _latest_task_status(request, course_key_string, view_func=None):
    """
    Get the most recent link check status update for the specified course/library
    key.
    """
    args = {'course_key_string': course_key_string}
    name = CourseLinkCheckTask.generate_name(args)
    task_status = UserTaskStatus.objects.filter(name=name)
    for status_filter in STATUS_FILTERS:
        task_status = status_filter().filter_queryset(request, task_status, view_func)
    return task_status.order_by('-created').first()
