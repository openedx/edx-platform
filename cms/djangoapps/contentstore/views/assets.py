import logging
from functools import partial

from django.http import HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django_future.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from edxmako.shortcuts import render_to_response
from cache_toolbox.core import del_cached_content

from xmodule.contentstore.django import contentstore
from xmodule.modulestore.django import modulestore
from xmodule.modulestore import Location
from xmodule.contentstore.content import StaticContent
from xmodule.util.date_utils import get_default_time_display
from xmodule.modulestore import InvalidLocationError
from xmodule.exceptions import NotFoundError
from django.core.exceptions import PermissionDenied
from xmodule.modulestore.django import loc_mapper
from .access import has_access
from xmodule.modulestore.locator import BlockUsageLocator

from util.json_request import JsonResponse
from django.http import HttpResponseNotFound
import json
from django.utils.translation import ugettext as _
from pymongo import DESCENDING


__all__ = ['assets_handler']


@login_required
@ensure_csrf_cookie
def assets_handler(request, tag=None, course_id=None, branch=None, version_guid=None, block=None, asset_id=None):
    """
    The restful handler for assets.
    It allows retrieval of all the assets (as an HTML page), as well as uploading new assets,
    deleting assets, and changing the "locked" state of an asset.

    GET
        html: return html page of all course assets (note though that a range of assets can be requested using start
        and max query parameters)
        json: not currently supported
    POST
        json: create (or update?) an asset. The only updating that can be done is changing the lock state.
    PUT
        json: update the locked state of an asset
    DELETE
        json: delete an asset
    """
    location = BlockUsageLocator(course_id=course_id, branch=branch, version_guid=version_guid, usage_id=block)
    if not has_access(request.user, location):
        raise PermissionDenied()

    if 'application/json' in request.META.get('HTTP_ACCEPT', 'application/json'):
        if request.method == 'GET':
            raise NotImplementedError('coming soon')
        else:
            return _update_asset(request, location, asset_id)
    elif request.method == 'GET':  # assume html
        return _asset_index(request, location)
    else:
        return HttpResponseNotFound()


def _asset_index(request, location):
    """
    Display an editable asset library.

    Supports start (0-based index into the list of assets) and max query parameters.
    """
    old_location = loc_mapper().translate_locator_to_location(location)

    course_module = modulestore().get_item(old_location)
    maxresults = request.REQUEST.get('max', None)
    start = request.REQUEST.get('start', None)
    course_reference = StaticContent.compute_location(old_location.org, old_location.course, old_location.name)
    if maxresults is not None:
        maxresults = int(maxresults)
        start = int(start) if start else 0
        assets = contentstore().get_all_content_for_course(
            course_reference, start=start, maxresults=maxresults,
            sort=[('uploadDate', DESCENDING)]
        )
    else:
        assets = contentstore().get_all_content_for_course(
            course_reference, sort=[('uploadDate', DESCENDING)]
        )

    asset_json = []
    for asset in assets:
        asset_id = asset['_id']
        asset_location = StaticContent.compute_location(asset_id['org'], asset_id['course'], asset_id['name'])
        # note, due to the schema change we may not have a 'thumbnail_location' in the result set
        _thumbnail_location = asset.get('thumbnail_location', None)
        thumbnail_location = Location(_thumbnail_location) if _thumbnail_location is not None else None

        asset_locked = asset.get('locked', False)
        asset_json.append(_get_asset_json(asset['displayname'], asset['uploadDate'], asset_location, thumbnail_location, asset_locked))

    return render_to_response('asset_index.html', {
        'context_course': course_module,
        'asset_list': json.dumps(asset_json),
        'asset_callback_url': location.url_reverse('assets/', '')
    })


@require_POST
@ensure_csrf_cookie
@login_required
def _upload_asset(request, location):
    '''
    This method allows for POST uploading of files into the course asset
    library, which will be supported by GridFS in MongoDB.
    '''
    old_location = loc_mapper().translate_locator_to_location(location)

    # Does the course actually exist?!? Get anything from it to prove its
    # existence
    try:
        modulestore().get_item(old_location)
    except:
        # no return it as a Bad Request response
        logging.error('Could not find course' + old_location)
        return HttpResponseBadRequest()

    # compute a 'filename' which is similar to the location formatting, we're
    # using the 'filename' nomenclature since we're using a FileSystem paradigm
    # here. We're just imposing the Location string formatting expectations to
    # keep things a bit more consistent
    upload_file = request.FILES['file']
    filename = upload_file.name
    mime_type = upload_file.content_type

    content_loc = StaticContent.compute_location(old_location.org, old_location.course, filename)

    chunked = upload_file.multiple_chunks()
    sc_partial = partial(StaticContent, content_loc, filename, mime_type)
    if chunked:
        content = sc_partial(upload_file.chunks())
        tempfile_path = upload_file.temporary_file_path()
    else:
        content = sc_partial(upload_file.read())
        tempfile_path = None

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

    locked = getattr(content, 'locked', False)
    response_payload = {
        'asset': _get_asset_json(content.name, readback.last_modified_at, content.location, content.thumbnail_location, locked),
        'msg': _('Upload completed')
    }

    return JsonResponse(response_payload)


@require_http_methods(("DELETE", "POST", "PUT"))
@login_required
@ensure_csrf_cookie
def _update_asset(request, location, asset_id):
    """
    restful CRUD operations for a course asset.
    Currently only DELETE, POST, and PUT methods are implemented.

    asset_id: the URL of the asset (used by Backbone as the id)
    """
    def get_asset_location(asset_id):
        """ Helper method to get the location (and verify it is valid). """
        try:
            return StaticContent.get_location_from_path(asset_id)
        except InvalidLocationError as err:
            # return a 'Bad Request' to browser as we have a malformed Location
            return JsonResponse({"error": err.message}, status=400)

    if request.method == 'DELETE':
        loc = get_asset_location(asset_id)
        # Make sure the item to delete actually exists.
        try:
            content = contentstore().find(loc)
        except NotFoundError:
            return JsonResponse(status=404)

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
                logging.warning('Could not delete thumbnail: ' + content.thumbnail_location)

        # delete the original
        contentstore().delete(content.get_id())
        # remove from cache
        del_cached_content(content.location)
        return JsonResponse()

    elif request.method in ('PUT', 'POST'):
        if 'file' in request.FILES:
            return _upload_asset(request, location)
        else:
            # Update existing asset
            try:
                modified_asset = json.loads(request.body)
            except ValueError:
                return HttpResponseBadRequest()
            asset_id = modified_asset['url']
            asset_location = get_asset_location(asset_id)
            contentstore().set_attr(asset_location, 'locked', modified_asset['locked'])
            # Delete the asset from the cache so we check the lock status the next time it is requested.
            del_cached_content(asset_location)
            return JsonResponse(modified_asset, status=201)


def _get_asset_json(display_name, date, location, thumbnail_location, locked):
    """
    Helper method for formatting the asset information to send to client.
    """
    asset_url = StaticContent.get_url_path_from_location(location)
    return {
        'display_name': display_name,
        'date_added': get_default_time_display(date),
        'url': asset_url,
        'portable_url': StaticContent.get_static_path_from_location(location),
        'thumbnail': StaticContent.get_url_path_from_location(thumbnail_location) if thumbnail_location is not None else None,
        'locked': locked,
        # Needed for Backbone delete/update.
        'id': asset_url
    }
