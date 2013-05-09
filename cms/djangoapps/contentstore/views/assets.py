from django.http import HttpResponse, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django_future.csrf import ensure_csrf_cookie

from xmodule.contentstore.content import StaticContent
from access import get_location_and_verify_access
from xmodule.util.date_utils import get_default_time_display
from mitxmako.shortcuts import render_to_response


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
        id = asset['_id']
        display_info = {}
        display_info['displayname'] = asset['displayname']
        display_info['uploadDate'] = get_default_time_display(asset['uploadDate'].timetuple())

        asset_location = StaticContent.compute_location(id['org'], id['course'], id['name'])
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
        'upload_asset_callback_url': upload_asset_callback_url
    })


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
                        'uploadDate': get_default_time_display(readback.last_modified_at.timetuple()),
                        'url': StaticContent.get_url_path_from_location(content.location),
                        'thumb_url': StaticContent.get_url_path_from_location(thumbnail_location) if thumbnail_content is not None else None,
                        'msg': 'Upload completed'
                        }

    response = HttpResponse(json.dumps(response_payload))
    response['asset_url'] = StaticContent.get_url_path_from_location(content.location)
    return response

