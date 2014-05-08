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
from xmodule.modulestore.django import modulestore, loc_mapper
from xmodule.modulestore.locator import BlockUsageLocator
from xmodule.modulestore.xml_importer import import_from_xml
from xmodule.modulestore.xml_exporter import export_to_xml

from .access import has_course_access
from extract_tar import safetar_extractall
from student import auth
from student.roles import CourseInstructorRole, CourseStaffRole, GlobalStaff
from util.json_request import JsonResponse


__all__ = ['import_handler', 'import_status_handler', 'export_handler']


log = logging.getLogger(__name__)


# Regex to capture Content-Range header ranges.
CONTENT_RE = re.compile(r"(?P<start>\d{1,11})-(?P<stop>\d{1,11})/(?P<end>\d{1,11})")


@login_required
@ensure_csrf_cookie
@require_http_methods(("GET", "POST", "PUT"))
def import_handler(request, tag=None, package_id=None, branch=None, version_guid=None, block=None):
    """
    The restful handler for importing a course.

    GET
        html: return html page for import page
        json: not supported
    POST or PUT
        json: import a course via the .tar.gz file specified in request.FILES
    """
    location = BlockUsageLocator(package_id=package_id, branch=branch, version_guid=version_guid, block_id=block)
    if not has_course_access(request.user, location):
        raise PermissionDenied()

    old_location = loc_mapper().translate_locator_to_location(location)

    if 'application/json' in request.META.get('HTTP_ACCEPT', 'application/json'):
        if request.method == 'GET':
            raise NotImplementedError('coming soon')
        else:
            data_root = path(settings.GITHUB_REPO_ROOT)
            course_subdir = "{0}-{1}-{2}".format(old_location.org, old_location.course, old_location.name)
            course_dir = data_root / course_subdir

            filename = request.FILES['course-data'].name
            if not filename.endswith('.tar.gz'):
                return JsonResponse(
                    {
                        'ErrMsg': _('We only support uploading a .tar.gz file.'),
                        'Stage': 1
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
                    log.warning(
                        "Reported range %s does not match size downloaded so far %s",
                        content_range['start'],
                        size
                    )
                    return JsonResponse(
                        {
                            'ErrMsg': _('File upload corrupted. Please try again'),
                            'Stage': 1
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
                                  "url": location.url_reverse('import'),
                                  "thumbnailUrl": ""
                              }]
                })

            else:   # This was the last chunk.

                # Use sessions to keep info about import progress
                session_status = request.session.setdefault("import_status", {})
                key = location.package_id + filename
                session_status[key] = 1
                request.session.modified = True

                # Do everything from now on in a try-finally block to make sure
                # everything is properly cleaned up.
                try:

                    tar_file = tarfile.open(temp_filepath)
                    try:
                        safetar_extractall(tar_file, (course_dir + '/').encode('utf-8'))
                    except SuspiciousOperation as exc:
                        return JsonResponse(
                            {
                                'ErrMsg': 'Unsafe tar file. Aborting import.',
                                'SuspiciousFileOperationMsg': exc.args[0],
                                'Stage': 1
                            },
                            status=400
                        )
                    finally:
                        tar_file.close()

                    session_status[key] = 2
                    request.session.modified = True

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
                        return JsonResponse(
                            {

                                'ErrMsg': _('Could not find the course.xml file in the package.'),
                                'Stage': 2
                            },
                            status=415
                        )

                    logging.debug('found course.xml at {0}'.format(dirpath))

                    if dirpath != course_dir:
                        for fname in os.listdir(dirpath):
                            shutil.move(dirpath / fname, course_dir)

                    _module_store, course_items = import_from_xml(
                        modulestore('direct'),
                        settings.GITHUB_REPO_ROOT,
                        [course_subdir],
                        load_error_modules=False,
                        static_content_store=contentstore(),
                        target_location_namespace=old_location,
                        draft_store=modulestore()
                    )

                    new_location = course_items[0].location
                    logging.debug('new course at {0}'.format(new_location))

                    session_status[key] = 3
                    request.session.modified = True

                # Send errors to client with stage at which error occurred.
                except Exception as exception:   # pylint: disable=W0703
                    log.exception(
                        "error importing course"
                    )
                    return JsonResponse(
                        {
                            'ErrMsg': str(exception),
                            'Stage': session_status[key]
                        },
                        status=400
                    )

                finally:
                    shutil.rmtree(course_dir)

                return JsonResponse({'Status': 'OK'})
    elif request.method == 'GET':  # assume html
        course_module = modulestore().get_item(old_location)
        return render_to_response('import.html', {
            'context_course': course_module,
            'successful_import_redirect_url': location.url_reverse("course"),
            'import_status_url': location.url_reverse("import_status", "fillerName"),
        })
    else:
        return HttpResponseNotFound()


@require_GET
@ensure_csrf_cookie
@login_required
def import_status_handler(request, tag=None, package_id=None, branch=None, version_guid=None, block=None, filename=None):
    """
    Returns an integer corresponding to the status of a file import. These are:

        0 : No status info found (import done or upload still in progress)
        1 : Extracting file
        2 : Validating.
        3 : Importing to mongo

    """
    location = BlockUsageLocator(package_id=package_id, branch=branch, version_guid=version_guid, block_id=block)
    if not has_course_access(request.user, location):
        raise PermissionDenied()

    try:
        session_status = request.session["import_status"]
        status = session_status[location.package_id + filename]
    except KeyError:
        status = 0

    return JsonResponse({"ImportStatus": status})


@ensure_csrf_cookie
@login_required
@require_http_methods(("GET",))
def export_handler(request, tag=None, package_id=None, branch=None, version_guid=None, block=None):
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
    location = BlockUsageLocator(package_id=package_id, branch=branch, version_guid=version_guid, block_id=block)
    if not has_course_access(request.user, location):
        raise PermissionDenied()

    old_location = loc_mapper().translate_locator_to_location(location)
    course_module = modulestore().get_item(old_location)

    # an _accept URL parameter will be preferred over HTTP_ACCEPT in the header.
    requested_format = request.REQUEST.get('_accept', request.META.get('HTTP_ACCEPT', 'text/html'))

    export_url = location.url_reverse('export') + '?_accept=application/x-tgz'
    if 'application/x-tgz' in requested_format:
        name = old_location.name
        export_file = NamedTemporaryFile(prefix=name + '.', suffix=".tar.gz")
        root_dir = path(mkdtemp())

        try:
            export_to_xml(modulestore('direct'), contentstore(), old_location, root_dir, name, modulestore())

            logging.debug('tar file being generated at {0}'.format(export_file.name))
            with tarfile.open(name=export_file.name, mode='w:gz') as tar_file:
                tar_file.add(root_dir / name, arcname=name)
        except SerializationError, e:
            logging.exception('There was an error exporting course {0}. {1}'.format(course_module.location, unicode(e)))
            unit = None
            failed_item = None
            parent = None
            try:
                failed_item = modulestore().get_instance(course_module.location.course_id, e.location)
                parent_locs = modulestore().get_parent_locations(failed_item.location, course_module.location.course_id)

                if len(parent_locs) > 0:
                    parent = modulestore().get_item(parent_locs[0])
                    if parent.location.category == 'vertical':
                        unit = parent
            except:
                # if we have a nested exception, then we'll show the more generic error message
                pass

            unit_locator = loc_mapper().translate_location(old_location.course_id, parent.location, False, True)

            return render_to_response('export.html', {
                'context_course': course_module,
                'in_err': True,
                'raw_err_msg': str(e),
                'failed_module': failed_item,
                'unit': unit,
                'edit_unit_url': unit_locator.url_reverse("unit") if parent else "",
                'course_home_url': location.url_reverse("course"),
                'export_url': export_url
            })
        except Exception, e:
            logging.exception('There was an error exporting course {0}. {1}'.format(course_module.location, unicode(e)))
            return render_to_response('export.html', {
                'context_course': course_module,
                'in_err': True,
                'unit': None,
                'raw_err_msg': str(e),
                'course_home_url': location.url_reverse("course"),
                'export_url': export_url
            })
        finally:
            shutil.rmtree(root_dir / name)

        wrapper = FileWrapper(export_file)
        response = HttpResponse(wrapper, content_type='application/x-tgz')
        response['Content-Disposition'] = 'attachment; filename=%s' % os.path.basename(export_file.name)
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
