"""
These views handle all actions in Studio related to import and exporting of
courses
"""
import logging
import os
import re
import shutil
import tarfile
from path import path
from tempfile import mkdtemp

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import SuspiciousOperation, PermissionDenied
from django.core.files.temp import NamedTemporaryFile
from django.core.servers.basehttp import FileWrapper
from django.http import HttpResponse, HttpResponseNotFound
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_http_methods, require_GET

from django_future.csrf import ensure_csrf_cookie
from edxmako.shortcuts import render_to_response
from xmodule.contentstore.django import contentstore
from xmodule.exceptions import SerializationError
from xmodule.modulestore.django import modulestore
from opaque_keys.edx.keys import CourseKey
from xmodule.modulestore.xml_importer import import_from_xml
from xmodule.modulestore.xml_exporter import export_to_xml

from .access import has_course_access

from extract_tar import safetar_extractall
from student import auth
from student.roles import CourseInstructorRole, CourseStaffRole, GlobalStaff
from util.json_request import JsonResponse

from contentstore.utils import reverse_course_url, reverse_usage_url


__all__ = ['import_handler', 'import_status_handler', 'export_handler']


log = logging.getLogger(__name__)


# Regex to capture Content-Range header ranges.
CONTENT_RE = re.compile(r"(?P<start>\d{1,11})-(?P<stop>\d{1,11})/(?P<end>\d{1,11})")


# pylint: disable=unused-argument
@login_required
@ensure_csrf_cookie
@require_http_methods(("GET", "POST", "PUT"))
def import_handler(request, course_key_string):
    """
    The restful handler for importing a course.

    GET
        html: return html page for import page
        json: not supported
    POST or PUT
        json: import a course via the .tar.gz file specified in request.FILES
    """
    course_key = CourseKey.from_string(course_key_string)
    if not has_course_access(request.user, course_key):
        raise PermissionDenied()

    if 'application/json' in request.META.get('HTTP_ACCEPT', 'application/json'):
        if request.method == 'GET':
            raise NotImplementedError('coming soon')
        else:
            # Do everything in a try-except block to make sure everything is properly cleaned up.
            try:
                data_root = path(settings.GITHUB_REPO_ROOT)
                course_subdir = "{0}-{1}-{2}".format(course_key.org, course_key.course, course_key.run)
                course_dir = data_root / course_subdir
                filename = request.FILES['course-data'].name

                # Use sessions to keep info about import progress
                session_status = request.session.setdefault("import_status", {})
                key = unicode(course_key) + filename
                _save_request_status(request, key, 0)
                if not filename.endswith('.tar.gz'):
                    _save_request_status(request, key, -1)
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

                logging.debug('importing course to {0}'.format(temp_filepath))

                # Get upload chunks byte ranges
                try:
                    matches = CONTENT_RE.search(request.META["HTTP_CONTENT_RANGE"])
                    content_range = matches.groupdict()
                except KeyError:    # Single chunk
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
                        _save_request_status(request, key, -1)
                        log.warning(
                            "Reported range %s does not match size downloaded so far %s",
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

                with open(temp_filepath, mode) as temp_file:
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
                            "url": reverse_course_url('import_handler', course_key),
                            "thumbnailUrl": ""
                        }]
                    })
            # Send errors to client with stage at which error occurred.
            except Exception as exception:   # pylint: disable=W0703
                _save_request_status(request, key, -1)
                if course_dir.isdir():
                    shutil.rmtree(course_dir)
                    log.info("Course import {0}: Temp data cleared".format(course_key))

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

            # try-finally block for proper clean up after receiving last chunk.
            try:
                # This was the last chunk.
                log.info("Course import {0}: Upload complete".format(course_key))
                _save_request_status(request, key, 1)

                tar_file = tarfile.open(temp_filepath)
                try:
                    safetar_extractall(tar_file, (course_dir + '/').encode('utf-8'))
                except SuspiciousOperation as exc:
                    _save_request_status(request, key, -1)
                    return JsonResponse(
                        {
                            'ErrMsg': 'Unsafe tar file. Aborting import.',
                            'SuspiciousFileOperationMsg': exc.args[0],
                            'Stage': -1
                        },
                        status=400
                    )
                finally:
                    tar_file.close()

                log.info("Course import {0}: Uploaded file extracted".format(course_key))
                _save_request_status(request, key, 2)

                # find the 'course.xml' file
                def get_all_files(directory):
                    """
                    For each file in the directory, yield a 2-tuple of (file-name,
                    directory-path)
                    """
                    for dirpath, _dirnames, filenames in os.walk(directory):
                        for filename in filenames:
                            yield (filename, dirpath)

                def get_dir_for_fname(directory, filename):
                    """
                    Returns the dirpath for the first file found in the directory
                    with the given name.  If there is no file in the directory with
                    the specified name, return None.
                    """
                    for fname, dirpath in get_all_files(directory):
                        if fname == filename:
                            return dirpath
                    return None

                fname = "course.xml"
                dirpath = get_dir_for_fname(course_dir, fname)
                if not dirpath:
                    _save_request_status(request, key, -2)
                    return JsonResponse(
                        {

                            'ErrMsg': _('Could not find the course.xml file in the package.'),
                            'Stage': -2
                        },
                        status=415
                    )

                dirpath = os.path.relpath(dirpath, data_root)
                logging.debug('found course.xml at {0}'.format(dirpath))

                log.info("Course import {0}: Extracted file verified".format(course_key))
                _save_request_status(request, key, 3)

                course_items = import_from_xml(
                    modulestore(),
                    request.user.id,
                    settings.GITHUB_REPO_ROOT,
                    [dirpath],
                    load_error_modules=False,
                    static_content_store=contentstore(),
                    target_course_id=course_key,
                )

                new_location = course_items[0].location
                logging.debug('new course at {0}'.format(new_location))

                log.info("Course import {0}: Course import successful".format(course_key))
                _save_request_status(request, key, 4)

            # Send errors to client with stage at which error occurred.
            except Exception as exception:   # pylint: disable=W0703
                log.exception(
                    "error importing course"
                )
                return JsonResponse(
                    {
                        'ErrMsg': str(exception),
                        'Stage': -session_status[key]
                    },
                    status=400
                )

            finally:
                if course_dir.isdir():
                    shutil.rmtree(course_dir)
                    log.info("Course import {0}: Temp data cleared".format(course_key))
                # set failed stage number with negative sign in case of unsuccessful import
                if session_status[key] != 4:
                    _save_request_status(request, key, -abs(session_status[key]))

            return JsonResponse({'Status': 'OK'})
    elif request.method == 'GET':  # assume html
        course_module = modulestore().get_course(course_key)
        return render_to_response('import.html', {
            'context_course': course_module,
            'successful_import_redirect_url': reverse_course_url('course_handler', course_key),
            'import_status_url': reverse_course_url("import_status_handler", course_key, kwargs={'filename': "fillerName"}),
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


# pylint: disable=unused-argument
@require_GET
@ensure_csrf_cookie
@login_required
def import_status_handler(request, course_key_string, filename=None):
    """
    Returns an integer corresponding to the status of a file import. These are:

        -X : Import unsuccessful due to some error with X as stage [0-3]
        0 : No status info found (import done or upload still in progress)
        1 : Extracting file
        2 : Validating.
        3 : Importing to mongo
        4 : Import successful

    """
    course_key = CourseKey.from_string(course_key_string)
    if not has_course_access(request.user, course_key):
        raise PermissionDenied()

    try:
        session_status = request.session["import_status"]
        status = session_status[course_key_string + filename]
    except KeyError:
        status = 0

    return JsonResponse({"ImportStatus": status})


# pylint: disable=unused-argument
@ensure_csrf_cookie
@login_required
@require_http_methods(("GET",))
def export_handler(request, course_key_string):
    """
    The restful handler for exporting a course.

    GET
        html: return html page for import page
        application/x-tgz: return tar.gz file containing exported course
        json: not supported

    Note that there are 2 ways to request the tar.gz file. The request header can specify
    application/x-tgz via HTTP_ACCEPT, or a query parameter can be used (?_accept=application/x-tgz).

    If the tar.gz file has been requested but the export operation fails, an HTML page will be returned
    which describes the error.
    """
    course_key = CourseKey.from_string(course_key_string)
    if not has_course_access(request.user, course_key):
        raise PermissionDenied()

    course_module = modulestore().get_course(course_key)

    # an _accept URL parameter will be preferred over HTTP_ACCEPT in the header.
    requested_format = request.REQUEST.get('_accept', request.META.get('HTTP_ACCEPT', 'text/html'))

    export_url = reverse_course_url('export_handler', course_key) + '?_accept=application/x-tgz'
    if 'application/x-tgz' in requested_format:
        name = course_module.url_name
        export_file = NamedTemporaryFile(prefix=name + '.', suffix=".tar.gz")
        root_dir = path(mkdtemp())

        try:
            export_to_xml(modulestore(), contentstore(), course_module.id, root_dir, name)

            logging.debug(u'tar file being generated at {0}'.format(export_file.name))
            with tarfile.open(name=export_file.name, mode='w:gz') as tar_file:
                tar_file.add(root_dir / name, arcname=name)
        except SerializationError as exc:
            log.exception(u'There was an error exporting course %s', course_module.id)
            unit = None
            failed_item = None
            parent = None
            try:
                failed_item = modulestore().get_item(exc.location)
                parent_loc = modulestore().get_parent_location(failed_item.location)

                if parent_loc is not None:
                    parent = modulestore().get_item(parent_loc)
                    if parent.location.category == 'vertical':
                        unit = parent
            except:  # pylint: disable=bare-except
                # if we have a nested exception, then we'll show the more generic error message
                pass

            return render_to_response('export.html', {
                'context_course': course_module,
                'in_err': True,
                'raw_err_msg': str(exc),
                'failed_module': failed_item,
                'unit': unit,
                'edit_unit_url': reverse_usage_url("container_handler", parent.location) if parent else "",
                'course_home_url': reverse_course_url("course_handler", course_key),
                'export_url': export_url
            })
        except Exception as exc:
            log.exception('There was an error exporting course %s', course_module.id)
            return render_to_response('export.html', {
                'context_course': course_module,
                'in_err': True,
                'unit': None,
                'raw_err_msg': str(exc),
                'course_home_url': reverse_course_url("course_handler", course_key),
                'export_url': export_url
            })
        finally:
            shutil.rmtree(root_dir / name)

        wrapper = FileWrapper(export_file)
        response = HttpResponse(wrapper, content_type='application/x-tgz')
        response['Content-Disposition'] = 'attachment; filename=%s' % os.path.basename(export_file.name.encode('utf-8'))
        response['Content-Length'] = os.path.getsize(export_file.name)
        return response

    elif 'text/html' in requested_format:
        return render_to_response('export.html', {
            'context_course': course_module,
            'export_url': export_url
        })

    else:
        # Only HTML or x-tgz request formats are supported (no JSON).
        return HttpResponse(status=406)
