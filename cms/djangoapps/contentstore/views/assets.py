import logging
import json
import os
import tarfile
import shutil
import cgi
import re
from functools import partial
from tempfile import mkdtemp
from path import path

from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django_future.csrf import ensure_csrf_cookie
from django.core.urlresolvers import reverse
from django.core.servers.basehttp import FileWrapper
from django.core.files.temp import NamedTemporaryFile
from django.views.decorators.http import require_POST, require_http_methods

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
from xmodule.exceptions import NotFoundError, SerializationError

from .access import get_location_and_verify_access
from util.json_request import JsonResponse


__all__ = ['asset_index', 'upload_asset']

def assets_to_json_dict(assets):
    """
    Transform the results of a contentstore query into something appropriate
    for output via JSON.
    """
    ret = []
    for asset in assets:
        obj = {
            "name": asset.get("displayname", ""),
            "chunkSize": asset.get("chunkSize", 0),
            "path": asset.get("filename", ""),
            "length": asset.get("length", 0),
        }
        uploaded = asset.get("uploadDate")
        if uploaded:
            obj["uploaded"] = uploaded.isoformat()
        thumbnail = asset.get("thumbnail_location")
        if thumbnail:
            obj["thumbnail"] = thumbnail
        id_info = asset.get("_id")
        if id_info:
            obj["id"] = "/{tag}/{org}/{course}/{revision}/{category}/{name}" \
                .format(
                    org=id_info.get("org", ""),
                    course=id_info.get("course", ""),
                    revision=id_info.get("revision", ""),
                    tag=id_info.get("tag", ""),
                    category=id_info.get("category", ""),
                    name=id_info.get("name", ""),
            )
        ret.append(obj)
    return ret


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

    if request.META.get('HTTP_ACCEPT', "").startswith("application/json"):
        return JsonResponse(assets_to_json_dict(assets))

    asset_display = []
    for asset in assets:
        asset_id = asset['_id']
        display_info = {}
        display_info['displayname'] = asset['displayname']
        display_info['uploadDate'] = get_default_time_display(asset['uploadDate'])

        asset_location = StaticContent.compute_location(asset_id['org'], asset_id['course'], asset_id['name'])
        display_info['url'] = StaticContent.get_url_path_from_location(asset_location)
        display_info['portable_url'] = StaticContent.get_static_path_from_location(asset_location)

        # note, due to the schema change we may not have a 'thumbnail_location' in the result set
        _thumbnail_location = asset.get('thumbnail_location', None)
        thumbnail_location = Location(_thumbnail_location) if _thumbnail_location is not None else None
        display_info['thumb_url'] = StaticContent.get_url_path_from_location(thumbnail_location) if thumbnail_location is not None else None

        asset_display.append(display_info)

    return render_to_response('asset_index.html', {
        'context_course': course_module,
        'assets': asset_display,
        'upload_asset_callback_url': upload_asset_callback_url,
        'remove_asset_callback_url': reverse('remove_asset', kwargs={
            'org': org,
            'course': course,
            'name': name
        })
    })


@require_POST
@ensure_csrf_cookie
@login_required
def upload_asset(request, org, course, coursename):
    '''
    This method allows for POST uploading of files into the course asset
    library, which will be supported by GridFS in MongoDB.
    '''
    # construct a location from the passed in path
    location = get_location_and_verify_access(request, org, course, coursename)

    # Does the course actually exist?!? Get anything from it to prove its
    # existence
    try:
        modulestore().get_item(location)
    except:
        # no return it as a Bad Request response
        logging.error('Could not find course' + location)
        return HttpResponseBadRequest()

    if 'files[]' not in request.FILES:
        return HttpResponseBadRequest()

    # compute a 'filename' which is similar to the location formatting, we're
    # using the 'filename' nomenclature since we're using a FileSystem paradigm
    # here. We're just imposing the Location string formatting expectations to
    # keep things a bit more consistent
    upload_file = request.FILES['files[]']
    filename = upload_file.name
    mime_type = upload_file.content_type

    content_loc = StaticContent.compute_location(org, course, filename)

    chunked = upload_file.multiple_chunks()
    sc_partial = partial(StaticContent, content_loc, filename, mime_type)
    if chunked:
        content = sc_partial(upload_file.chunks())
        tempfile_path = upload_file.temporary_file_path()
    else:
        content = sc_partial(upload_file.read())
        tempfile_path = None

    thumbnail_content = None
    thumbnail_location = None

    # first let's see if a thumbnail can be created
    (thumbnail_content, thumbnail_location) = contentstore().generate_thumbnail(
            content,
            tempfile_path=tempfile_path
    )

    # delete cached thumbnail even if one couldn't be created this time (else
    # the old thumbnail will continue to show)
    del_cached_content(thumbnail_location)
    # now store thumbnail location only if we could create it
    if thumbnail_content is not None:
        content.thumbnail_location = thumbnail_location

    # then commit the content
    contentstore().save(content)
    del_cached_content(content.location)

    # readback the saved content - we need the database timestamp
    readback = contentstore().find(content.location)

    response_payload = {
            'displayname': content.name,
            'uploadDate': get_default_time_display(readback.last_modified_at),
            'url': StaticContent.get_url_path_from_location(content.location),
            'portable_url': StaticContent.get_static_path_from_location(content.location),
            'thumb_url': StaticContent.get_url_path_from_location(thumbnail_location)
                if thumbnail_content is not None else None,
            'msg': 'Upload completed'
    }

    response = JsonResponse(response_payload)
    return response


@ensure_csrf_cookie
@login_required
def remove_asset(request, org, course, name):
    '''
    This method will perform a 'soft-delete' of an asset, which is basically to
    copy the asset from the main GridFS collection and into a Trashcan
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


