import logging
from functools import partial
import math
import json

from django.http import HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django_future.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST
from django.conf import settings

from edxmako.shortcuts import render_to_response
from cache_toolbox.core import del_cached_content

from contentstore.utils import reverse_course_url
from xmodule.contentstore.django import contentstore
from xmodule.modulestore.django import modulestore
from xmodule.contentstore.content import StaticContent
from xmodule.exceptions import NotFoundError
from django.core.exceptions import PermissionDenied
from opaque_keys.edx.keys import CourseKey, AssetKey

from util.date_utils import get_default_time_display
from util.json_request import JsonResponse
from django.http import HttpResponseNotFound
from django.utils.translation import ugettext as _
from pymongo import ASCENDING, DESCENDING
from .access import has_course_access
from xmodule.modulestore.exceptions import ItemNotFoundError

__all__ = ['assets_handler']


# pylint: disable=unused-argument
@login_required
@ensure_csrf_cookie
def assets_handler(request, course_key_string=None, asset_key_string=None):
    """
    The restful handler for assets.
    It allows retrieval of all the assets (as an HTML page), as well as uploading new assets,
    deleting assets, and changing the "locked" state of an asset.

    GET
        html: return an html page which will show all course assets. Note that only the asset container
            is returned and that the actual assets are filled in with a client-side request.
        json: returns a page of assets. The following parameters are supported:
            page: the desired page of results (defaults to 0)
            page_size: the number of items per page (defaults to 50)
            sort: the asset field to sort by (defaults to "date_added")
            direction: the sort direction (defaults to "descending")
    POST
        json: create (or update?) an asset. The only updating that can be done is changing the lock state.
    PUT
        json: update the locked state of an asset
    DELETE
        json: delete an asset
    """
    course_key = CourseKey.from_string(course_key_string)
    if not has_course_access(request.user, course_key):
        raise PermissionDenied()

    response_format = request.REQUEST.get('format', 'html')
    if response_format == 'json' or 'application/json' in request.META.get('HTTP_ACCEPT', 'application/json'):
        if request.method == 'GET':
            return _assets_json(request, course_key)
        else:
            asset_key = AssetKey.from_string(asset_key_string) if asset_key_string else None
            return _update_asset(request, course_key, asset_key)
    elif request.method == 'GET':  # assume html
        return _asset_index(request, course_key)
    else:
        return HttpResponseNotFound()


def _asset_index(request, course_key):
    """
    Display an editable asset library.

    Supports start (0-based index into the list of assets) and max query parameters.
    """
    course_module = modulestore().get_course(course_key)

    return render_to_response('asset_index.html', {
        'context_course': course_module,
        'asset_callback_url': reverse_course_url('assets_handler', course_key)
    })


def _assets_json(request, course_key):
    """
    Display an editable asset library.

    Supports start (0-based index into the list of assets) and max query parameters.
    """
    requested_page = int(request.REQUEST.get('page', 0))
    requested_page_size = int(request.REQUEST.get('page_size', 50))
    requested_sort = request.REQUEST.get('sort', 'date_added')
    sort_direction = DESCENDING
    if request.REQUEST.get('direction', '').lower() == 'asc':
        sort_direction = ASCENDING

    # Convert the field name to the Mongo name
    if requested_sort == 'date_added':
        requested_sort = 'uploadDate'
    elif requested_sort == 'display_name':
        requested_sort = 'displayname'
    sort = [(requested_sort, sort_direction)]

    current_page = max(requested_page, 0)
    start = current_page * requested_page_size
    assets, total_count = _get_assets_for_page(request, course_key, current_page, requested_page_size, sort)
    end = start + len(assets)

    # If the query is beyond the final page, then re-query the final page so that at least one asset is returned
    if requested_page > 0 and start >= total_count:
        current_page = int(math.floor((total_count - 1) / requested_page_size))
        start = current_page * requested_page_size
        assets, total_count = _get_assets_for_page(request, course_key, current_page, requested_page_size, sort)
        end = start + len(assets)

    asset_json = []
    for asset in assets:
        asset_location = asset['asset_key']
        # note, due to the schema change we may not have a 'thumbnail_location' in the result set
        thumbnail_location = asset.get('thumbnail_location', None)
        if thumbnail_location:
            thumbnail_location = course_key.make_asset_key('thumbnail', thumbnail_location[4])

        asset_locked = asset.get('locked', False)
        asset_json.append(_get_asset_json(asset['displayname'], asset['uploadDate'], asset_location, thumbnail_location, asset_locked))

    return JsonResponse({
        'start': start,
        'end': end,
        'page': current_page,
        'pageSize': requested_page_size,
        'totalCount': total_count,
        'assets': asset_json,
        'sort': requested_sort,
    })


def _get_assets_for_page(request, course_key, current_page, page_size, sort):
    """
    Returns the list of assets for the specified page and page size.
    """
    start = current_page * page_size

    return contentstore().get_all_content_for_course(
        course_key, start=start, maxresults=page_size, sort=sort
    )


@require_POST
@ensure_csrf_cookie
@login_required
def _upload_asset(request, course_key):
    '''
    This method allows for POST uploading of files into the course asset
    library, which will be supported by GridFS in MongoDB.
    '''
    # Does the course actually exist?!? Get anything from it to prove its
    # existence
    try:
        modulestore().get_course(course_key)
    except ItemNotFoundError:
        # no return it as a Bad Request response
        logging.error("Could not find course: %s", course_key)
        return HttpResponseBadRequest()

    # compute a 'filename' which is similar to the location formatting, we're
    # using the 'filename' nomenclature since we're using a FileSystem paradigm
    # here. We're just imposing the Location string formatting expectations to
    # keep things a bit more consistent
    upload_file = request.FILES['file']
    filename = upload_file.name
    mime_type = upload_file.content_type

    content_loc = StaticContent.compute_location(course_key, filename)

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
def _update_asset(request, course_key, asset_key):
    """
    restful CRUD operations for a course asset.
    Currently only DELETE, POST, and PUT methods are implemented.

    asset_path_encoding: the odd /c4x/org/course/category/name repr of the asset (used by Backbone as the id)
    """
    if request.method == 'DELETE':
        # Make sure the item to delete actually exists.
        try:
            content = contentstore().find(asset_key)
        except NotFoundError:
            return JsonResponse(status=404)

        # ok, save the content into the trashcan
        contentstore('trashcan').save(content)

        # see if there is a thumbnail as well, if so move that as well
        if content.thumbnail_location is not None:
            # We are ignoring the value of the thumbnail_location-- we only care whether
            # or not a thumbnail has been stored, and we can now easily create the correct path.
            thumbnail_location = course_key.make_asset_key('thumbnail', asset_key.name)
            try:
                thumbnail_content = contentstore().find(thumbnail_location)
                contentstore('trashcan').save(thumbnail_content)
                # hard delete thumbnail from origin
                contentstore().delete(thumbnail_content.get_id())
                # remove from any caching
                del_cached_content(thumbnail_location)
            except:
                logging.warning('Could not delete thumbnail: %s', thumbnail_location)

        # delete the original
        contentstore().delete(content.get_id())
        # remove from cache
        del_cached_content(content.location)
        return JsonResponse()

    elif request.method in ('PUT', 'POST'):
        if 'file' in request.FILES:
            return _upload_asset(request, course_key)
        else:
            # Update existing asset
            try:
                modified_asset = json.loads(request.body)
            except ValueError:
                return HttpResponseBadRequest()
            contentstore().set_attr(asset_key, 'locked', modified_asset['locked'])
            # Delete the asset from the cache so we check the lock status the next time it is requested.
            del_cached_content(asset_key)
            return JsonResponse(modified_asset, status=201)


def _get_asset_json(display_name, date, location, thumbnail_location, locked):
    """
    Helper method for formatting the asset information to send to client.
    """
    asset_url = _add_slash(location.to_deprecated_string())
    external_url = settings.LMS_BASE + asset_url
    return {
        'display_name': display_name,
        'date_added': get_default_time_display(date),
        'url': asset_url,
        'external_url': external_url,
        'portable_url': StaticContent.get_static_path_from_location(location),
        'thumbnail': _add_slash(unicode(thumbnail_location)) if thumbnail_location else None,
        'locked': locked,
        # Needed for Backbone delete/update.
        'id': unicode(location)
    }


def _add_slash(url):
    if not url.startswith('/'):
        url = '/' + url  # TODO - re-address this once LMS-11198 is tackled.
    return url
