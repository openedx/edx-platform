"""
These views handle all actions in Studio related to import and exporting of
courses
"""
import logging
import os
import tarfile
import shutil
import re
from tempfile import mkdtemp
from path import path
from contextlib import contextmanager

from django.conf import settings
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django_future.csrf import ensure_csrf_cookie
from django.core.urlresolvers import reverse
from django.core.servers.basehttp import FileWrapper
from django.core.files.temp import NamedTemporaryFile
from django.views.decorators.http import require_http_methods

from mitxmako.shortcuts import render_to_response
from auth.authz import create_all_course_groups

from xmodule.modulestore.xml_importer import import_from_xml
from xmodule.contentstore.django import contentstore
from xmodule.modulestore.xml_exporter import export_to_xml
from xmodule.modulestore.django import modulestore
from xmodule.modulestore import Location
from xmodule.exceptions import SerializationError

from .access import get_location_and_verify_access
from util.json_request import JsonResponse


__all__ = ['import_course', 'generate_export_course', 'export_course']

log = logging.getLogger(__name__)


# Regex to capture Content-Range header ranges.
CONTENT_RE = re.compile(r"(?P<start>\d{1,11})-(?P<stop>\d{1,11})/(?P<end>\d{1,11})")


@ensure_csrf_cookie
@require_http_methods(("GET", "POST", "PUT"))
@login_required
def import_course(request, org, course, name):
    """
    This method will handle a POST request to upload and import a .tar.gz file
    into a specified course
    """
    location = get_location_and_verify_access(request, org, course, name)

    @contextmanager
    def wfile(filename, dirname):
        """
        A with-context that creates `filename` on entry and removes it on exit.
        `filename` is truncted on creation. Additionally removes dirname on
        exit.
        """
        open("file", "w").close()
        try:
            yield filename
        finally:
            os.remove(filename)
            shutil.rmtree(dirname)

    if request.method == 'POST':

        data_root = path(settings.GITHUB_REPO_ROOT)
        course_subdir = "{0}-{1}-{2}".format(org, course, name)
        course_dir = data_root / course_subdir

        filename = request.FILES['course-data'].name
        if not filename.endswith('.tar.gz'):
            return JsonResponse(
                {'ErrMsg': 'We only support uploading a .tar.gz file.'},
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
                    {'ErrMsg': 'File upload corrupted. Please try again'},
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
                    "url": reverse('import_course', kwargs={
                        'org': location.org,
                        'course': location.course,
                        'name': location.name
                    }),
                    "thumbnailUrl": ""
                }]
            })

        else:   # This was the last chunk.

            # 'Lock' with status info.
            status_file = data_root / (course + filename + ".lock")

            # Do everything from now on in a with-context, to be sure we've
            # properly cleaned up.
            with wfile(status_file, course_dir):

                with open(status_file, 'w+') as sf:
                    sf.write("Extracting")

                tar_file = tarfile.open(temp_filepath)
                tar_file.extractall(course_dir + '/')

                with open(status_file, 'w+') as sf:
                    sf.write("Verifying")

                # find the 'course.xml' file
                dirpath = None

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
                        {'ErrMsg': 'Could not find the course.xml file in the package.'},
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
                    target_location_namespace=location,
                    draft_store=modulestore()
                )

                logging.debug('new course at {0}'.format(course_items[0].location))

                with open(status_file, 'w') as sf:
                    sf.write("Updating course")

                create_all_course_groups(request.user, course_items[0].location)
                logging.debug('created all course groups at {0}'.format(course_items[0].location))

            return JsonResponse({'Status': 'OK'})
    else:
        course_module = modulestore().get_item(location)

        return render_to_response('import.html', {
            'context_course': course_module,
            'successful_import_redirect_url': reverse('course_index', kwargs={
                'org': location.org,
                'course': location.course,
                'name': location.name,
            })
        })


@ensure_csrf_cookie
@login_required
def generate_export_course(request, org, course, name):
    """
    This method will serialize out a course to a .tar.gz file which contains a
    XML-based representation of the course
    """
    location = get_location_and_verify_access(request, org, course, name)
    course_module = modulestore().get_instance(location.course_id, location)
    loc = Location(location)
    export_file = NamedTemporaryFile(prefix=name + '.', suffix=".tar.gz")

    root_dir = path(mkdtemp())

    try:
        export_to_xml(modulestore('direct'), contentstore(), loc, root_dir, name, modulestore())
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

        return render_to_response('export.html', {
            'context_course': course_module,
            'successful_import_redirect_url': '',
            'in_err': True,
            'raw_err_msg': str(e),
            'failed_module': failed_item,
            'unit': unit,
            'edit_unit_url': reverse('edit_unit', kwargs={
                'location': parent.location
            }) if parent else '',
            'course_home_url': reverse('course_index', kwargs={
                'org': org,
                'course': course,
                'name': name
            })
        })
    except Exception, e:
        logging.exception('There was an error exporting course {0}. {1}'.format(course_module.location, unicode(e)))
        return render_to_response('export.html', {
            'context_course': course_module,
            'successful_import_redirect_url': '',
            'in_err': True,
            'unit': None,
            'raw_err_msg': str(e),
            'course_home_url': reverse('course_index', kwargs={
                'org': org,
                'course': course,
                'name': name
            })
        })

    logging.debug('tar file being generated at {0}'.format(export_file.name))
    tar_file = tarfile.open(name=export_file.name, mode='w:gz')
    tar_file.add(root_dir / name, arcname=name)
    tar_file.close()

    # remove temp dir
    shutil.rmtree(root_dir / name)

    wrapper = FileWrapper(export_file)
    response = HttpResponse(wrapper, content_type='application/x-tgz')
    response['Content-Disposition'] = 'attachment; filename=%s' % os.path.basename(export_file.name)
    response['Content-Length'] = os.path.getsize(export_file.name)
    return response


@ensure_csrf_cookie
@login_required
def export_course(request, org, course, name):
    """
    This method serves up the 'Export Course' page
    """
    location = get_location_and_verify_access(request, org, course, name)

    course_module = modulestore().get_item(location)

    return render_to_response('export.html', {
        'context_course': course_module,
        'successful_import_redirect_url': ''
    })
