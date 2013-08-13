"""
**Views for transcripts ajax calls**.

Module do not support rollback (pressing "Cancel" button in Studio)
All user changes are saved immediately.
"""
import os
import logging
import json

from django.http import HttpResponse, Http404
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
    YOUTUBE_API,
    save_subs_to_store,
)

from ..utils import get_modulestore
from .access import has_access

log = logging.getLogger(__name__)


def save_module(item):
    """
    Proceed with additional save operations.
    """
    item.save()
    store = get_modulestore(Location(item.id))
    store.update_metadata(item.id, own_metadata(item))
    return item


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

    video_list = request.POST.get('video_list')
    if not video_list:
        log.error('POST data without video names.')
        return JsonResponse(response)

    video_list = json.loads(video_list)
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
    if video_list:
        sub_attr = source_subs_name

        # Assuming we uploaded subs for speed = 1.0
        # Generate subs and save for all videos names to storage
        status, __ = generate_subs_from_source(
            {1: sub_attr},
            source_subs_ext,
            source_subs_filedata,
            item)
        if status:
            statuses = {}
            for video_dict in video_list:
                video_name = video_dict['video']
                # creating transcripts for every video source
                # in case that some of them would be deleted
                statuses[video_name] = _rename_transcript(video_name, sub_attr, item)

            # name to write to sub field
            selected_name = video_list[0]['video']

            if statuses[selected_name]:  # write names to sub attribute files
                item.sub = selected_name
                item = save_module(item)
                response['subs'] = item.sub
                response['status'] = 'Success'

    else:
        log.error('Empty video sources.')
        return JsonResponse(response)

    return JsonResponse(response)


def download_transcripts(request):
    """
    Test
    """
    item_location = request.GET.get('id')
    if not item_location:
        log.error('GET data without "id" property.')
        raise Http404

    subs_id = request.GET.get('subs_id')
    if not subs_id:
        log.error('GET data without "subs_id" property.')
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

    filename = 'subs_{0}.srt.sjson'.format(subs_id)
    content_location = StaticContent.compute_location(
        item.location.org, item.location.course, filename)
    try:
        sjson_transcripts = contentstore().find(content_location)
        log.debug("Downloading subs for {} id".format(subs_id))
        str_subs = generate_srt_from_sjson(json.loads(sjson_transcripts.data), speed=1.0)
        if str_subs is None:
            log.error('generate_srt_from_sjson produces no subtitles')
            raise Http404
        response = HttpResponse(str_subs, content_type='application/x-subrip')
        response['Content-Disposition'] = 'attachment; filename="{0}.srt"'.format(subs_id)
        return response
    except NotFoundError:
        log.debug("Can't find content in storage for {} subs".format(subs_id))
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
        'html5_equal': False,
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

    filename = 'subs_{0}.srt.sjson'.format(item.sub)
    content_location = StaticContent.compute_location(
        item.location.org, item.location.course, filename)
    try:
        local_transcripts = contentstore().find(content_location).data
        transcripts_presence['current_item_subs'] = item.sub
    except NotFoundError:
        pass

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
    html5_subs = []
    for html5_id in videos['html5']:
        filename = 'subs_{0}.srt.sjson'.format(html5_id)
        content_location = StaticContent.compute_location(
            item.location.org, item.location.course, filename)
        try:
            html5_subs.append(contentstore().find(content_location).data)
            transcripts_presence['html5_local'].append(html5_id)
        except NotFoundError:
            log.debug("Can't find transcripts in storage for non-youtube video_id: {}".format(html5_id))
        if len(html5_subs) == 2:  # check html5 transcripts for equality
            transcripts_presence['html5_equal'] = json.loads(html5_subs[0]) == json.loads(html5_subs[1])

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
        if transcripts_presence['html5_local']:  # can be 1 or 2 html5 videos
            if len(transcripts_presence['html5_local']) == 1 or transcripts_presence['html5_equal']:
                command = 'found'
                subs = transcripts_presence['html5_local'][0]
            else:
                command = 'choose'
        else:  # html5 source have no subtitles
            # check if item sub has subtitles
            if transcripts_presence['current_item_subs'] and not transcripts_presence['is_youtube_mode']:
                log.debug("Command is use existing {} subs".format(transcripts_presence['current_item_subs']))
                command = 'use_existing'
                # subs = transcripts_presence['current_item_subs']
            else:
                command = 'not_found'
    log.debug('Resulted command: {}, current transcripys: {}, youtube mode: {}'.format(command, transcripts_presence['current_item_subs'], transcripts_presence['is_youtube_mode']))
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

    if item.sub != html5_id:  # update sub value
        item.sub = html5_id
        item = save_module(item)
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
    item.sub = youtube_id
    item = save_module(item)
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


def _rename_transcript(new_name, old_name, item, delete_old=False):
    """
    Renames old_name to new_name transcripts files in storage.
    """
    filename = 'subs_{0}.srt.sjson'.format(old_name)
    content_location = StaticContent.compute_location(
        item.location.org, item.location.course, filename)
    try:
        transcripts = contentstore().find(content_location).data
        save_subs_to_store(json.loads(transcripts), new_name, item)
        item.sub = new_name
        item = save_module(item)
    except NotFoundError:
        log.debug("Can't find transcripts in storage for id: {}".format(old_name))
        return False
    else:
        if delete_old:
            remove_subs_from_store(old_name, item)
        return True


def rename_transcripts(request):
    """
    Renames html5 subtitles
    """

    response = {
        'status': 'Error',
        'subs': '',
    }

    validation_status, __, videos, item = validate_transcripts_data(request)
    if not validation_status:
        return JsonResponse(response)

    old_name = item.sub

    statuses = {}

    # copy subtitles for every html5 source
    for new_name in videos['html5'].keys():
        statuses[new_name] = _rename_transcript(new_name, old_name, item)

    if any(statuses):
        response['status'] = 'Success'
        response['subs'] = item.sub
        log.debug("Updated item.sub to {}".format(item.sub))
    return JsonResponse(response)
