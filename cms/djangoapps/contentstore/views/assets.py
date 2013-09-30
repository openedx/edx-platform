import logging
from functools import partial

from django.http import HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django_future.csrf import ensure_csrf_cookie
from django.core.urlresolvers import reverse
from django.views.decorators.http import require_POST

from mitxmako.shortcuts import render_to_response
from cache_toolbox.core import del_cached_content

from xmodule.contentstore.django import contentstore
from xmodule.modulestore.django import modulestore
from xmodule.modulestore import Location
from xmodule.contentstore.content import StaticContent
from xmodule.util.date_utils import get_default_time_display
from xmodule.modulestore import InvalidLocationError
from xmodule.exceptions import NotFoundError

from .access import get_location_and_verify_access
from util.json_request import JsonResponse
import json
from django.utils.translation import ugettext as _


__all__ = ['asset_index', 'upload_asset']


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
        'upload_asset_callback_url': upload_asset_callback_url,
        'update_asset_callback_url': reverse('update_asset', kwargs={
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

    if 'file' not in request.FILES:
        return HttpResponseBadRequest()

    # compute a 'filename' which is similar to the location formatting, we're
    # using the 'filename' nomenclature since we're using a FileSystem paradigm
    # here. We're just imposing the Location string formatting expectations to
    # keep things a bit more consistent
    upload_file = request.FILES['file']
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
def update_asset(request, org, course, name, asset_id):
    """
    restful CRUD operations for a course asset.
    Currently only DELETE, POST, and PUT methods are implemented.

    org, course, name: Attributes of the Location for the item to edit
    asset_id: the URL of the asset (used by Backbone as the id)
    """
    def get_asset_location(asset_id):
        """ Helper method to get the location (and verify it is valid). """
        try:
            return StaticContent.get_location_from_path(asset_id)
        except InvalidLocationError as err:
            # return a 'Bad Request' to browser as we have a malformed Location
            return JsonResponse({"error": err.message}, status=400)

    get_location_and_verify_access(request, org, course, name)

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
        # We don't support creation of new assets through this
        # method-- just changing the locked state.
        modified_asset = json.loads(request.body)
        asset_id = modified_asset['url']
        location = get_asset_location(asset_id)
        contentstore().set_attr(location, 'locked', modified_asset['locked'])
        # Delete the asset from the cache so we check the lock status the next time it is requested.
        del_cached_content(location)

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
