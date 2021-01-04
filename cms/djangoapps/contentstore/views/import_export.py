"""
These views handle all actions in Studio related to import and exporting of
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
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_http_methods
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locator import LibraryLocator
from path import Path as path
from six import text_type
from storages.backends.s3boto import S3BotoStorage
from user_tasks.conf import settings as user_tasks_settings
from user_tasks.models import UserTaskArtifact, UserTaskStatus

from common.djangoapps.edxmako.shortcuts import render_to_response
from common.djangoapps.student.auth import has_course_author_access
from common.djangoapps.util.json_request import JsonResponse
from common.djangoapps.util.views import ensure_valid_course_key
from xmodule.modulestore.django import modulestore

from ..storage import course_import_export_storage
from ..tasks import CourseExportTask, CourseImportTask, export_olx, import_olx
from ..utils import reverse_course_url, reverse_library_url

__all__ = [
    'import_handler', 'import_status_handler',
    'export_handler', 'export_output_handler', 'export_status_handler',
]

log = logging.getLogger(__name__)

# Regex to capture Content-Range header ranges.
CONTENT_RE = re.compile(r"(?P<start>\d{1,11})-(?P<stop>\d{1,11})/(?P<end>\d{1,11})")

STATUS_FILTERS = user_tasks_settings.USER_TASKS_STATUS_FILTERS


@transaction.non_atomic_requests
@login_required
@ensure_csrf_cookie
@require_http_methods(("GET", "POST", "PUT"))
@ensure_valid_course_key
def import_handler(request, course_key_string):
    """
    The restful handler for importing a course.

    GET
        html: return html page for import page
        json: not supported
    POST or PUT
        json: import a course via the .tar.gz file specified in request.FILES
    """
    courselike_key = CourseKey.from_string(course_key_string)
    library = isinstance(courselike_key, LibraryLocator)
    if library:
        successful_url = reverse_library_url('library_handler', courselike_key)
        context_name = 'context_library'
        courselike_module = modulestore().get_library(courselike_key)
    else:
        successful_url = reverse_course_url('course_handler', courselike_key)
        context_name = 'context_course'
        courselike_module = modulestore().get_course(courselike_key)
    if not has_course_author_access(request.user, courselike_key):
        raise PermissionDenied()

    if 'application/json' in request.META.get('HTTP_ACCEPT', 'application/json'):
        if request.method == 'GET':
            raise NotImplementedError('coming soon')
        else:
            return _write_chunk(request, courselike_key)
    elif request.method == 'GET':  # assume html
        status_url = reverse_course_url(
            "import_status_handler", courselike_key, kwargs={'filename': "fillerName"}
        )
        return render_to_response('import.html', {
            context_name: courselike_module,
            'successful_import_redirect_url': successful_url,
            'import_status_url': status_url,
            'library': isinstance(courselike_key, LibraryLocator)
        })
    else:
        return HttpResponseNotFound()


def _save_request_status(request, key, status):
    """
    Save import status for a course in request session
    """
    session_status = request.session.get('import_status')
    if session_status is None:
        session_status = request.session.setdefault("import_status", {})

    session_status[key] = status
    request.session.save()


def _write_chunk(request, courselike_key):
    """
    Write the OLX file data chunk from the given request to the local filesystem.
    """
    # Upload .tar.gz to local filesystem for one-server installations not using S3 or Swift
    data_root = path(settings.GITHUB_REPO_ROOT)
    subdir = base64.urlsafe_b64encode(repr(courselike_key).encode('utf-8')).decode('utf-8')
    course_dir = data_root / subdir
    filename = request.FILES['course-data'].name

    courselike_string = text_type(courselike_key) + filename
    # Do everything in a try-except block to make sure everything is properly cleaned up.
    try:
        # Use sessions to keep info about import progress
        _save_request_status(request, courselike_string, 0)

        if not filename.endswith('.tar.gz'):
            _save_request_status(request, courselike_string, -1)
            return JsonResponse(
                {
                    'ErrMsg': _('We only support uploading a .tar.gz file.'),
                    'Stage': -1
                },
                status=415
            )

        temp_filepath = course_dir / filename
        if not course_dir.isdir():
            os.mkdir(course_dir)

        logging.debug(u'importing course to {0}'.format(temp_filepath))

        # Get upload chunks byte ranges
        try:
            matches = CONTENT_RE.search(request.META["HTTP_CONTENT_RANGE"])
            content_range = matches.groupdict()
        except KeyError:  # Single chunk
            # no Content-Range header, so make one that will work
            content_range = {'start': 0, 'stop': 1, 'end': 2}

        # stream out the uploaded files in chunks to disk
        if int(content_range['start']) == 0:
            mode = "wb+"
        else:
            mode = "ab+"
            size = os.path.getsize(temp_filepath)
            # Check to make sure we haven't missed a chunk
            # This shouldn't happen, even if different instances are handling
            # the same session, but it's always better to catch errors earlier.
            if size < int(content_range['start']):
                _save_request_status(request, courselike_string, -1)
                log.warning(
                    u"Reported range %s does not match size downloaded so far %s",
                    content_range['start'],
                    size
                )
                return JsonResponse(
                    {
                        'ErrMsg': _('File upload corrupted. Please try again'),
                        'Stage': -1
                    },
                    status=409
                )
            # The last request sometimes comes twice. This happens because
            # nginx sends a 499 error code when the response takes too long.
            elif size > int(content_range['stop']) and size == int(content_range['end']):
                return JsonResponse({'ImportStatus': 1})

        with open(temp_filepath, mode) as temp_file:  # pylint: disable=W6005
            for chunk in request.FILES['course-data'].chunks():
                temp_file.write(chunk)

        size = os.path.getsize(temp_filepath)

        if int(content_range['stop']) != int(content_range['end']) - 1:
            # More chunks coming
            return JsonResponse({
                "files": [{
                    "name": filename,
                    "size": size,
                    "deleteUrl": "",
                    "deleteType": "",
                    "url": reverse_course_url('import_handler', courselike_key),
                    "thumbnailUrl": ""
                }]
            })

        log.info(u"Course import %s: Upload complete", courselike_key)
        with open(temp_filepath, 'rb') as local_file:  # pylint: disable=W6005
            django_file = File(local_file)
            storage_path = course_import_export_storage.save(u'olx_import/' + filename, django_file)
        import_olx.delay(
            request.user.id, text_type(courselike_key), storage_path, filename, request.LANGUAGE_CODE)

    # Send errors to client with stage at which error occurred.
    except Exception as exception:  # pylint: disable=broad-except
        _save_request_status(request, courselike_string, -1)
        if course_dir.isdir():
            shutil.rmtree(course_dir)
            log.info(u"Course import %s: Temp data cleared", courselike_key)

        log.exception(
            "error importing course"
        )
        return JsonResponse(
            {
                'ErrMsg': str(exception),
                'Stage': -1
            },
            status=400
        )

    return JsonResponse({'ImportStatus': 1})


@transaction.non_atomic_requests
@require_GET
@ensure_csrf_cookie
@login_required
@ensure_valid_course_key
def import_status_handler(request, course_key_string, filename=None):
    """
    Returns an integer corresponding to the status of a file import. These are:

        -X : Import unsuccessful due to some error with X as stage [0-3]
        0 : No status info found (import done or upload still in progress)
        1 : Unpacking
        2 : Verifying
        3 : Updating
        4 : Import successful

    """
    course_key = CourseKey.from_string(course_key_string)
    if not has_course_author_access(request.user, course_key):
        raise PermissionDenied()

    # The task status record is authoritative once it's been created
    args = {u'course_key_string': course_key_string, u'archive_name': filename}
    name = CourseImportTask.generate_name(args)
    task_status = UserTaskStatus.objects.filter(name=name)
    for status_filter in STATUS_FILTERS:
        task_status = status_filter().filter_queryset(request, task_status, import_status_handler)
    task_status = task_status.order_by(u'-created').first()
    if task_status is None:
        # The task hasn't been initialized yet; did we store info in the session already?
        try:
            session_status = request.session["import_status"]
            status = session_status[course_key_string + filename]
        except KeyError:
            status = 0
    elif task_status.state == UserTaskStatus.SUCCEEDED:
        status = 4
    elif task_status.state in (UserTaskStatus.FAILED, UserTaskStatus.CANCELED):
        status = max(-(task_status.completed_steps + 1), -3)
    else:
        status = min(task_status.completed_steps + 1, 3)

    return JsonResponse({"ImportStatus": status})


def send_tarball(tarball, size):
    """
    Renders a tarball to response, for use when sending a tar.gz file to the user.
    """
    wrapper = FileWrapper(tarball, settings.COURSE_EXPORT_DOWNLOAD_CHUNK_SIZE)
    response = StreamingHttpResponse(wrapper, content_type='application/x-tgz')
    response['Content-Disposition'] = u'attachment; filename=%s' % os.path.basename(tarball.name)
    response['Content-Length'] = size
    return response


@transaction.non_atomic_requests
@ensure_csrf_cookie
@login_required
@require_http_methods(('GET', 'POST'))
@ensure_valid_course_key
def export_handler(request, course_key_string):
    """
    The restful handler for exporting a course.

    GET
        html: return html page for import page
        json: not supported
    POST
        Start a Celery task to export the course

    The Studio UI uses a POST request to start the export asynchronously, with
    a link appearing on the page once it's ready.
    """
    course_key = CourseKey.from_string(course_key_string)
    if not has_course_author_access(request.user, course_key):
        raise PermissionDenied()

    if isinstance(course_key, LibraryLocator):
        courselike_module = modulestore().get_library(course_key)
        context = {
            'context_library': courselike_module,
            'courselike_home_url': reverse_library_url("library_handler", course_key),
            'library': True
        }
    else:
        courselike_module = modulestore().get_course(course_key)
        if courselike_module is None:
            raise Http404
        context = {
            'context_course': courselike_module,
            'courselike_home_url': reverse_course_url("course_handler", course_key),
            'library': False
        }
    context['status_url'] = reverse_course_url('export_status_handler', course_key)

    # an _accept URL parameter will be preferred over HTTP_ACCEPT in the header.
    requested_format = request.GET.get('_accept', request.META.get('HTTP_ACCEPT', 'text/html'))

    if request.method == 'POST':
        export_olx.delay(request.user.id, course_key_string, request.LANGUAGE_CODE)
        return JsonResponse({'ExportStatus': 1})
    elif 'text/html' in requested_format:
        return render_to_response('export.html', context)
    else:
        # Only HTML request format is supported (no JSON).
        return HttpResponse(status=406)


@transaction.non_atomic_requests
@require_GET
@ensure_csrf_cookie
@login_required
@ensure_valid_course_key
def export_status_handler(request, course_key_string):
    """
    Returns an integer corresponding to the status of a file export. These are:

        -X : Export unsuccessful due to some error with X as stage [0-3]
        0 : No status info found (export done or task not yet created)
        1 : Exporting
        2 : Compressing
        3 : Export successful

    If the export was successful, a URL for the generated .tar.gz file is also
    returned.
    """
    course_key = CourseKey.from_string(course_key_string)
    if not has_course_author_access(request.user, course_key):
        raise PermissionDenied()

    # The task status record is authoritative once it's been created
    task_status = _latest_task_status(request, course_key_string, export_status_handler)
    output_url = None
    error = None
    if task_status is None:
        # The task hasn't been initialized yet; did we store info in the session already?
        try:
            session_status = request.session["export_status"]
            status = session_status[course_key_string]
        except KeyError:
            status = 0
    elif task_status.state == UserTaskStatus.SUCCEEDED:
        status = 3
        artifact = UserTaskArtifact.objects.get(status=task_status, name='Output')
        if isinstance(artifact.file.storage, FileSystemStorage):
            output_url = reverse_course_url('export_output_handler', course_key)
        elif isinstance(artifact.file.storage, S3BotoStorage):
            filename = os.path.basename(artifact.file.name)
            disposition = u'attachment; filename="{}"'.format(filename)
            output_url = artifact.file.storage.url(artifact.file.name, response_headers={
                'response-content-disposition': disposition,
                'response-content-encoding': 'application/octet-stream',
                'response-content-type': 'application/x-tgz'
            })
        else:
            output_url = artifact.file.storage.url(artifact.file.name)
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

    response = {"ExportStatus": status}
    if output_url:
        response['ExportOutput'] = output_url
    elif error:
        response['ExportError'] = error
    return JsonResponse(response)


@transaction.non_atomic_requests
@require_GET
@ensure_csrf_cookie
@login_required
@ensure_valid_course_key
def export_output_handler(request, course_key_string):
    """
    Returns the OLX .tar.gz produced by a file export.  Only used in
    environments such as devstack where the output is stored in a local
    filesystem instead of an external service like S3.
    """
    course_key = CourseKey.from_string(course_key_string)
    if not has_course_author_access(request.user, course_key):
        raise PermissionDenied()

    task_status = _latest_task_status(request, course_key_string, export_output_handler)
    if task_status and task_status.state == UserTaskStatus.SUCCEEDED:
        artifact = None
        try:
            artifact = UserTaskArtifact.objects.get(status=task_status, name='Output')
            tarball = course_import_export_storage.open(artifact.file.name)
            return send_tarball(tarball, artifact.file.storage.size(artifact.file.name))
        except UserTaskArtifact.DoesNotExist:
            raise Http404
        finally:
            if artifact:
                artifact.file.close()
    else:
        raise Http404


def _latest_task_status(request, course_key_string, view_func=None):
    """
    Get the most recent export status update for the specified course/library
    key.
    """
    args = {u'course_key_string': course_key_string}
    name = CourseExportTask.generate_name(args)
    task_status = UserTaskStatus.objects.filter(name=name)
    for status_filter in STATUS_FILTERS:
        task_status = status_filter().filter_queryset(request, task_status, view_func)
    return task_status.order_by(u'-created').first()
