import logging
import json
import os
import tarfile
import shutil
from tempfile import mkdtemp
from path import path

from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django_future.csrf import ensure_csrf_cookie
from django.core.urlresolvers import reverse
from django.core.servers.basehttp import FileWrapper
from django.core.files.temp import NamedTemporaryFile

from mitxmako.shortcuts import render_to_response
from cache_toolbox.core import del_cached_content
from auth.authz import create_all_course_groups

from xmodule.modulestore.xml_importer import import_from_xml
from xmodule.contentstore.django import contentstore
from xmodule.modulestore.xml_exporter import export_to_xml
from xmodule.modulestore.django import modulestore
from xmodule.modulestore import Location
from xmodule.contentstore.content import StaticContent
from xmodule.util.date_utils import get_default_time_display
from xmodule.modulestore import InvalidLocationError
from xmodule.exceptions import NotFoundError

from ..utils import get_url_reverse
from .access import get_location_and_verify_access


__all__ = ['asset_index', 'upload_asset', 'import_course', 'generate_export_course', 'export_course']


@login_required
@ensure_csrf_cookie
def asset_index(request, org, course, name):
    """
    Display an editable asset library

    org, course, name: Attributes of the Location for the item to edit
    """
    location = get_location_and_verify_access(request, org, course, name)

    upload_asset_callback_url = reverse('upload_asset', kwargs={
        'org': org,
        'course': course,
        'coursename': name
    })

    course_module = modulestore().get_item(location)

    course_reference = StaticContent.compute_location(org, course, name)
    assets = contentstore().get_all_content_for_course(course_reference)

    # sort in reverse upload date order
    assets = sorted(assets, key=lambda asset: asset['uploadDate'], reverse=True)

    asset_display = []
    for asset in assets:
        asset_id = asset['_id']
        display_info = {}
        display_info['displayname'] = asset['displayname']
        display_info['uploadDate'] = get_default_time_display(asset['uploadDate'])

        asset_location = StaticContent.compute_location(asset_id['org'], asset_id['course'], asset_id['name'])
        display_info['url'] = StaticContent.get_url_path_from_location(asset_location)

        # note, due to the schema change we may not have a 'thumbnail_location' in the result set
        _thumbnail_location = asset.get('thumbnail_location', None)
        thumbnail_location = Location(_thumbnail_location) if _thumbnail_location is not None else None
        display_info['thumb_url'] = StaticContent.get_url_path_from_location(thumbnail_location) if thumbnail_location is not None else None

        asset_display.append(display_info)

    return render_to_response('asset_index.html', {
        'active_tab': 'assets',
        'context_course': course_module,
        'assets': asset_display,
        'upload_asset_callback_url': upload_asset_callback_url,
        'remove_asset_callback_url': reverse('remove_asset', kwargs={
            'org': org,
            'course': course,
            'name': name
        })
    })


@login_required
@ensure_csrf_cookie
def upload_asset(request, org, course, coursename):
    '''
    cdodge: this method allows for POST uploading of files into the course asset library, which will
    be supported by GridFS in MongoDB.
    '''
    if request.method != 'POST':
        # (cdodge) @todo: Is there a way to do a - say - 'raise Http400'?
        return HttpResponseBadRequest()

    # construct a location from the passed in path
    location = get_location_and_verify_access(request, org, course, coursename)

    # Does the course actually exist?!? Get anything from it to prove its existance

    try:
        modulestore().get_item(location)
    except:
        # no return it as a Bad Request response
        logging.error('Could not find course' + location)
        return HttpResponseBadRequest()

    if 'file' not in request.FILES:
        return HttpResponseBadRequest()

    # compute a 'filename' which is similar to the location formatting, we're using the 'filename'
    # nomenclature since we're using a FileSystem paradigm here. We're just imposing
    # the Location string formatting expectations to keep things a bit more consistent

    filename = request.FILES['file'].name
    mime_type = request.FILES['file'].content_type
    filedata = request.FILES['file'].read()

    content_loc = StaticContent.compute_location(org, course, filename)
    content = StaticContent(content_loc, filename, mime_type, filedata)

    # first let's see if a thumbnail can be created
    (thumbnail_content, thumbnail_location) = contentstore().generate_thumbnail(content)

    # delete cached thumbnail even if one couldn't be created this time (else the old thumbnail will continue to show)
    del_cached_content(thumbnail_location)
    # now store thumbnail location only if we could create it
    if thumbnail_content is not None:
        content.thumbnail_location = thumbnail_location

    # then commit the content
    contentstore().save(content)
    del_cached_content(content.location)

    # readback the saved content - we need the database timestamp
    readback = contentstore().find(content.location)

    response_payload = {'displayname': content.name,
                        'uploadDate': get_default_time_display(readback.last_modified_at),
                        'url': StaticContent.get_url_path_from_location(content.location),
                        'thumb_url': StaticContent.get_url_path_from_location(thumbnail_location) if thumbnail_content is not None else None,
                        'msg': 'Upload completed'
                        }

    response = HttpResponse(json.dumps(response_payload))
    response['asset_url'] = StaticContent.get_url_path_from_location(content.location)
    return response


@ensure_csrf_cookie
@login_required
def remove_asset(request, org, course, name):
    '''
    This method will perform a 'soft-delete' of an asset, which is basically to copy the asset from
    the main GridFS collection and into a Trashcan
    '''
    get_location_and_verify_access(request, org, course, name)

    location = request.POST['location']

    # make sure the location is valid
    try:
        loc = StaticContent.get_location_from_path(location)
    except InvalidLocationError:
        # return a 'Bad Request' to browser as we have a malformed Location
        response = HttpResponse()
        response.status_code = 400
        return response

    # also make sure the item to delete actually exists
    try:
        content = contentstore().find(loc)
    except NotFoundError:
        response = HttpResponse()
        response.status_code = 404
        return response

    # ok, save the content into the trashcan
    contentstore('trashcan').save(content)

    # see if there is a thumbnail as well, if so move that as well
    if content.thumbnail_location is not None:
        try:
            thumbnail_content = contentstore().find(content.thumbnail_location)
            contentstore('trashcan').save(thumbnail_content)
            # hard delete thumbnail from origin
            contentstore().delete(thumbnail_content.get_id())
            # remove from any caching
            del_cached_content(thumbnail_content.location)
        except:
            pass  # OK if this is left dangling

    # delete the original
    contentstore().delete(content.get_id())
    # remove from cache
    del_cached_content(content.location)

    return HttpResponse()


@ensure_csrf_cookie
@login_required
def import_course(request, org, course, name):

    location = get_location_and_verify_access(request, org, course, name)

    if request.method == 'POST':
        filename = request.FILES['course-data'].name

        if not filename.endswith('.tar.gz'):
            return HttpResponse(json.dumps({'ErrMsg': 'We only support uploading a .tar.gz file.'}))

        data_root = path(settings.GITHUB_REPO_ROOT)

        course_subdir = "{0}-{1}-{2}".format(org, course, name)
        course_dir = data_root / course_subdir
        if not course_dir.isdir():
            os.mkdir(course_dir)

        temp_filepath = course_dir / filename

        logging.debug('importing course to {0}'.format(temp_filepath))

        # stream out the uploaded files in chunks to disk
        temp_file = open(temp_filepath, 'wb+')
        for chunk in request.FILES['course-data'].chunks():
            temp_file.write(chunk)
        temp_file.close()

        tar_file = tarfile.open(temp_filepath)
        tar_file.extractall(course_dir + '/')

        # find the 'course.xml' file

        for dirpath, _dirnames, filenames in os.walk(course_dir):
            for files in filenames:
                if files == 'course.xml':
                    break
            if files == 'course.xml':
                break

        if files != 'course.xml':
            return HttpResponse(json.dumps({'ErrMsg': 'Could not find the course.xml file in the package.'}))

        logging.debug('found course.xml at {0}'.format(dirpath))

        if dirpath != course_dir:
            for fname in os.listdir(dirpath):
                shutil.move(dirpath / fname, course_dir)

        _module_store, course_items = import_from_xml(modulestore('direct'), settings.GITHUB_REPO_ROOT,
                                                      [course_subdir], load_error_modules=False,
                                                      static_content_store=contentstore(),
                                                      target_location_namespace=Location(location),
                                                      draft_store=modulestore())

        # we can blow this away when we're done importing.
        shutil.rmtree(course_dir)

        logging.debug('new course at {0}'.format(course_items[0].location))

        create_all_course_groups(request.user, course_items[0].location)

        return HttpResponse(json.dumps({'Status': 'OK'}))
    else:
        course_module = modulestore().get_item(location)

        return render_to_response('import.html', {
            'context_course': course_module,
            'active_tab': 'import',
            'successful_import_redirect_url': get_url_reverse('CourseOutline', course_module)
        })


@ensure_csrf_cookie
@login_required
def generate_export_course(request, org, course, name):
    location = get_location_and_verify_access(request, org, course, name)

    loc = Location(location)
    export_file = NamedTemporaryFile(prefix=name + '.', suffix=".tar.gz")

    root_dir = path(mkdtemp())

    # export out to a tempdir
    logging.debug('root = {0}'.format(root_dir))

    export_to_xml(modulestore('direct'), contentstore(), loc, root_dir, name, modulestore())

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

    location = get_location_and_verify_access(request, org, course, name)

    course_module = modulestore().get_item(location)

    return render_to_response('export.html', {
        'context_course': course_module,
        'active_tab': 'export',
        'successful_import_redirect_url': ''
    })
