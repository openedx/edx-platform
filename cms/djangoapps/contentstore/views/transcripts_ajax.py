"""
**Views for transcripts ajax calls**.

Module do not support rollback (pressing "Cancel" button in Studio)
All user changes are saved immediately.
"""
import os
import logging
import json

from django.http import HttpResponse, Http404
from django.template.defaultfilters import slugify
from django.core.exceptions import PermissionDenied

from xmodule.contentstore.content import StaticContent
from xmodule.exceptions import NotFoundError
from xmodule.modulestore.django import modulestore
from xmodule.contentstore.django import contentstore
from xmodule.modulestore.exceptions import ItemNotFoundError, InvalidLocationError
from xmodule.modulestore import Location
from xmodule.modulestore.inheritance import own_metadata

from util.json_request import JsonResponse

from ..transcripts_utils import (
    generate_subs_from_source,
    generate_srt_from_sjson, remove_subs_from_store,
    requests as rqsts,
    download_youtube_subs, get_transcripts_from_youtube,
    YOUTUBE_API
)

from ..utils import get_modulestore
from .access import has_access

log = logging.getLogger(__name__)


def upload_transcripts(request):
    """
    Upload transcripts for current module.

    returns: response dict::

        status: 'Success' or 'Error'
        subs: Value of uploaded and saved html5 sub field in  video item.
    """

    response = {
        'status': 'Error',
        'subs': '',
    }

    item_location = request.POST.get('id')
    if not item_location:
        log.error('POST data without "id" form data.')
        return JsonResponse(response)

    if 'file' not in request.FILES:
        log.error('POST data without "file" form data.')
        return JsonResponse(response)

    source_subs_filedata = request.FILES['file'].read()
    source_subs_filename = request.FILES['file'].name

    if '.' not in source_subs_filename:
        log.error("Undefined file extension.")
        return JsonResponse(response)

    basename = os.path.basename(source_subs_filename)
    source_subs_name = os.path.splitext(basename)[0]
    source_subs_ext = os.path.splitext(basename)[1][1:]

    try:
        item = modulestore().get_item(item_location)
    except (ItemNotFoundError, InvalidLocationError):
        log.error("Can't find item by location.")
        return JsonResponse(response)

    # Check permissions for this user within this course.
    if not has_access(request.user, item_location):
        raise PermissionDenied()

    if item.category != 'video':
        log.error('transcripts are supported only for "video" modules.')
        return JsonResponse(response)

    # Allow upload only if any video link is presented
    if item.youtube_id_1_0 or any(item.html5_sources):
        sub_attr = slugify(source_subs_name)

        # Assuming we uploaded subs for speed = 1.0
        # Generate subs and save
        status, __ = generate_subs_from_source(
            {1: sub_attr},
            source_subs_ext,
            source_subs_filedata,
            item)

        if status:  # saving generated subtitles
            item.sub = sub_attr
            item.save()
            store = get_modulestore(Location(item_location))
            store.update_metadata(item_location, own_metadata(item))
            response['subs'] = item.sub
            response['status'] = 'Success'

    else:
        log.error('Empty video sources.')
        return JsonResponse(response)

    return JsonResponse(response)


def download_transcripts(request):
    """
    Download transcripts from current module.
    """
    item_location = request.GET.get('id')
    if not item_location:
        log.error('GET data without "id" property.')
        raise Http404

    try:
        item = modulestore().get_item(item_location)
    except (ItemNotFoundError, InvalidLocationError):
        log.error("Can't find item by location.")
        raise Http404

    # Check permissions for this user within this course.
    if not has_access(request.user, item_location):
        raise PermissionDenied()

    if item.category != 'video':
        log.error('transcripts are supported only for video" modules.')
        raise Http404

    speed = 1
    subs_found = {'youtube': False, 'html5': False}
    # youtube subtitles has higher priority by design
    if item.youtube_id_1_0:  # downloading subtitles from youtube speed 1.0
        filename = 'subs_{0}.srt.sjson'.format(item.youtube_id_1_0)
        content_location = StaticContent.compute_location(
            item.location.org, item.location.course, filename)
        try:
            sjson_transcripts = contentstore().find(content_location)
            subs_found['youtube'] = True
            srt_file_name = item.youtube_id_1_0
            log.debug("Downloading subs from Youtube ids")
        except NotFoundError:
            log.debug("Can't find content in storage for youtube sub.")

    if item.sub and not subs_found['youtube']:  # downloading subtitles from html5
        filename = 'subs_{0}.srt.sjson'.format(item.sub)
        content_location = StaticContent.compute_location(
            item.location.org, item.location.course, filename)
        try:
            sjson_transcripts = contentstore().find(content_location)
            subs_found['html5'] = True
            srt_file_name = item.sub
            log.debug("Downloading subs from html5 subs ")
        except NotFoundError:
            log.error("Can't find content in storage for non-youtube sub.")

    if subs_found['youtube'] or subs_found['html5']:
        str_subs = generate_srt_from_sjson(json.loads(sjson_transcripts.data), speed)
        if str_subs is None:
            log.error('generate_srt_from_sjson produces no subtitles')
            raise Http404
        response = HttpResponse(str_subs, content_type='application/x-subrip')
        response['Content-Disposition'] = 'attachment; filename="{0}.srt"'.format(srt_file_name)
        return response
    else:
        log.error('No youtube 1.0 or html5 transcripts')
        raise Http404


def check_transcripts(request):
    """
    Check transcripts availability current module state..

    request.GET['data'] has key videos, which can contain any of the following::

        [
            {u'type': u'youtube', u'video': u'OEoXaMPEzfM', u'mode': u'youtube'},
            {u'type': u'html5',    u'video': u'video1',             u'mode': u'mp4'}
            {u'type': u'html5',    u'video': u'video2',             u'mode': u'webm'}
        ]

    Returns transcripts_presence object::

        html5_local: [], [True], [True], if html5 subtitles exist locally for any of [0-2] sources.
        is_youtube_mode: bool, if we have youtube_id, and as youtube_id are of higher priority, reflect this with flag.
        youtube_local: bool, if youtube transcripts exist locally.
        youtube_server: bool, if youtube transcripts exist on server.
        youtube_diff: bool, if youtube transcripts exist on youtube server, and are different from local youtube ones.
        current_item_subs: string, value of item.sub filed,
        status: string, 'Error' or 'Success'

    With `command` and `subs`.
    `command`: str,  action to front-end what to do and what show to user.
    `subs`: str, new value of item.sub field, that should be set in module.
    """
    transcripts_presence = {
        'html5_local': [],
        'is_youtube_mode': False,
        'youtube_local': False,
        'youtube_server': False,
        'youtube_diff': True,
        'current_item_subs': None,
        'status': 'Error',
    }
    validation_status, __, videos, item = validate_transcripts_data(request)
    if not validation_status:
        return JsonResponse(transcripts_presence)

    transcripts_presence['status'] = 'Success'
    transcripts_presence['current_item_subs'] = item.sub

    # Check for youtube transcripts presence
    youtube_id = videos.get('youtube', None)
    if youtube_id:
        transcripts_presence['is_youtube_mode'] = True

        # youtube local
        filename = 'subs_{0}.srt.sjson'.format(youtube_id)
        content_location = StaticContent.compute_location(
            item.location.org, item.location.course, filename)
        try:
            local_transcripts = contentstore().find(content_location).data
            transcripts_presence['youtube_local'] = True
        except NotFoundError:
            log.debug("Can't find transcripts in storage for youtube id: {}".format(youtube_id))

        # youtube server
        YOUTUBE_API['params']['v'] = youtube_id
        youtube_response = rqsts.get(
            YOUTUBE_API['url'],
            params=YOUTUBE_API['params']
        )
        if youtube_response.status_code == 200 and youtube_response.text:
            transcripts_presence['youtube_server'] = True
        #check youtube local and server transcripts for equality
        if transcripts_presence['youtube_server'] and transcripts_presence['youtube_local']:
            status, youtube_server_subs = get_transcripts_from_youtube(youtube_id)
            if status:  # check transcripts for equality
                if json.loads(local_transcripts) == youtube_server_subs:
                    transcripts_presence['youtube_diff'] = False

    # Check for html5 local transcripts presence
    for html5_id in videos['html5']:
        filename = 'subs_{0}.srt.sjson'.format(html5_id)
        content_location = StaticContent.compute_location(
            item.location.org, item.location.course, filename)
        try:
            contentstore().find(content_location)
            transcripts_presence['html5_local'].append(html5_id)
        except NotFoundError:
            log.debug("Can't find transcripts in storage for non-youtube video_id: {}".format(html5_id))

    command, subs_to_use = transcripts_logic(transcripts_presence, videos)
    transcripts_presence.update({
        'command': command,
        'subs': subs_to_use,
    })
    return JsonResponse(transcripts_presence)


def transcripts_logic(transcripts_presence, videos):
    """
    By transcripts status, figure what show to user:

    returns: `command` and `subs`.

    `command`: str,  action to front-end what to do and what show to user.
    `subs`: str, new value of item.sub field, that should be set in module.

    `command` is one of::

        replace: replace local youtube subtitles with server one's
        found: subtitles are found
        import: import subtitles from youtube server
        choose: choose one from two html5 subtitles
        not found: subtitles are not found
    """
    command = None

    # new value of item.sub field, that should be set in module.
    subs = ''

    # youtube transcripts are of high priority than html5 by design
    if (
            transcripts_presence['youtube_diff'] and
            transcripts_presence['youtube_local'] and
            transcripts_presence['youtube_server']):  # youtube server and local exist
        command = 'replace'
    elif transcripts_presence['youtube_local']:  # only youtube local exist
        command = 'found'
        subs = videos['youtube']
    elif transcripts_presence['youtube_server']:  # only youtube server exist
        command = 'import'
    else:  # html5 part
        if transcripts_presence['html5_local']:
            if len(transcripts_presence['html5_local']) == 1:
                command = 'found'
                subs = transcripts_presence['html5_local'][0]
            else:
                command = 'choose'
        else:
            command = 'not_found'

    return command, subs


def choose_transcripts(request):
    """
    Replaces html5 subtitles, presented for both html5 sources, with chosen one.

    Code removes rejected html5 subtitles and updates sub attribute with chosen html5_id.

    It does nothing with youtube id's.

    Returns: status (Success or Error) and resulted item.sub value
    """
    response = {
        'status': 'Error',
        'subs': '',
    }

    validation_status, data, videos, item = validate_transcripts_data(request)
    if not validation_status:
        return JsonResponse(response)

    html5_id = data.get('html5_id')

    # find rejected html5_id and remove appropriate subs from store
    html5_id_to_remove = [x for x in videos['html5'] if x != html5_id]
    if html5_id_to_remove:
        remove_subs_from_store(html5_id_to_remove, item)

    if item.sub != slugify(html5_id):  # update sub value
        item.sub = slugify(html5_id)
        item.save()
    response = {'status': 'Success',  'subs': item.sub}
    return JsonResponse(response)


def replace_transcripts(request):
    """
    Replaces all transcripts with youtube ones.

    Returns: status (Success or Error), resulted item.sub value and True for  is_youtube_mode value.
    """
    response = {
        'status': 'Error',
        'subs': '',
        'is_youtube_mode': True,
    }

    validation_status, __, videos, item = validate_transcripts_data(request)
    if not validation_status:
        return JsonResponse(response)

    youtube_id = videos['youtube']
    if not youtube_id:
        return JsonResponse(response)

    download_youtube_subs({1.0: youtube_id}, item)
    item.sub = slugify(youtube_id)
    item.save()
    response['status'] = 'Success'
    response['subs'] = item.sub
    return JsonResponse(response)


def validate_transcripts_data(request):
    """
    Validates, that request contains all proper data for transcripts processing.

    Returns parsed data from request and video item from storage.
    """
    validation_status = False

    data = json.loads(request.GET.get('data', '{}'))
    if not data:
        log.error('Incoming video data is empty.')
        return validation_status, None, {}, None

    item_location = data.get('id')
    try:
        item = modulestore().get_item(item_location)
    except (ItemNotFoundError, InvalidLocationError):
        log.error("Can't find item by location.")
        return validation_status, None, {}, None

    # Check permissions for this user within this course.
    if not has_access(request.user, item_location):
        raise PermissionDenied()

    if item.category != 'video':
        log.error('transcripts are supported only for "video" modules.')
        return validation_status, None, {}, None

    # parse data form request.GET.['data']['video'] to useful format
    videos = {'youtube': '', 'html5': {}}
    for video_data in data.get('videos'):
        if video_data['type'] == 'youtube':
            videos['youtube'] = video_data['video']
        else:  # do not add same html5 videos
            if videos['html5'].get('video') != video_data['video']:
                videos['html5'][video_data['video']] = video_data['mode']

    return True, data, videos, item
