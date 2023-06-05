"""
Actions manager for transcripts ajax calls.
+++++++++++++++++++++++++++++++++++++++++++

Module do not support rollback (pressing "Cancel" button in Studio)
All user changes are saved immediately.
"""


import copy
import json
import logging
import os

import requests
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.files.base import ContentFile
from django.http import Http404, HttpResponse
from django.utils.translation import ugettext as _
from edxval.api import create_external_video, create_or_update_video_transcript
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import UsageKey
from six import text_type

from cms.djangoapps.contentstore.views.videos import TranscriptProvider
from common.djangoapps.student.auth import has_course_author_access
from common.djangoapps.util.json_request import JsonResponse
from xmodule.contentstore.content import StaticContent
from xmodule.contentstore.django import contentstore
from xmodule.exceptions import NotFoundError
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError
from xmodule.video_module.transcripts_utils import (
    GetTranscriptsFromYouTubeException,
    Transcript,
    TranscriptsGenerationException,
    TranscriptsRequestValidationException,
    clean_video_id,
    download_youtube_subs,
    get_transcript,
    get_transcript_for_video,
    get_transcript_from_val,
    get_transcripts_from_youtube,
    youtube_video_transcript_name
)

__all__ = [
    'upload_transcripts',
    'download_transcripts',
    'check_transcripts',
    'choose_transcripts',
    'replace_transcripts',
    'rename_transcripts',
]

log = logging.getLogger(__name__)


def error_response(response, message, status_code=400):
    """
    Simplify similar actions: log message and return JsonResponse with message included in response.

    By default return 400 (Bad Request) Response.
    """
    log.debug(message)
    response['status'] = message
    return JsonResponse(response, status_code)


def link_video_to_component(video_component, user):
    """
    Links a VAL video to the video component.

    Arguments:
        video_component: video descriptor item.
        user: A requesting user.

    Returns:
        A cleaned Video ID.
    """
    edx_video_id = clean_video_id(video_component.edx_video_id)
    if not edx_video_id:
        edx_video_id = create_external_video(display_name=u'external video')
        video_component.edx_video_id = edx_video_id
        video_component.save_with_metadata(user)

    return edx_video_id


def save_video_transcript(edx_video_id, input_format, transcript_content, language_code):
    """
    Saves a video transcript to the VAL and its content to the configured django storage(DS).

    Arguments:
        edx_video_id: A Video ID to associate the transcript.
        input_format: Input transcript format for content being passed.
        transcript_content: Content of the transcript file
        language_code: transcript language code

    Returns:
        A boolean indicating whether the transcript was saved or not.
    """
    try:
        # Convert the transcript into the 'sjson' and upload it to
        # configured transcript storage. For example, S3.
        sjson_subs = Transcript.convert(
            content=transcript_content,
            input_format=input_format,
            output_format=Transcript.SJSON
        ).encode()
        create_or_update_video_transcript(
            video_id=edx_video_id,
            language_code=language_code,
            metadata={
                'provider': TranscriptProvider.CUSTOM,
                'file_format': Transcript.SJSON,
                'language_code': language_code
            },
            file_data=ContentFile(sjson_subs),
        )
        result = True
    except (TranscriptsGenerationException, UnicodeDecodeError):
        result = False

    return result


def validate_video_module(request, locator):
    """
    Validates video module given its locator and request. Also, checks
    if requesting user has course authoring access.

    Arguments:
        request: WSGI request.
        locator: video locator.

    Returns:
        A tuple containing error(or None) and video descriptor(i.e. if validation succeeds).

    Raises:
        PermissionDenied: if requesting user does not have access to author the video component.
    """
    error, item = None, None
    try:
        item = _get_item(request, {'locator': locator})
        if item.category != 'video':
            error = _(u'Transcripts are supported only for "video" modules.')
    except (InvalidKeyError, ItemNotFoundError):
        error = _(u'Cannot find item by locator.')

    return error, item


def validate_transcript_upload_data(request):
    """
    Validates video transcript file.

    Arguments:
        request: A WSGI request's data part.

    Returns:
        Tuple containing an error and validated data
        If there is a validation error then, validated data will be empty.
    """
    error, validated_data = None, {}
    data, files = request.POST, request.FILES
    video_locator = data.get('locator')
    edx_video_id = data.get('edx_video_id')
    if not video_locator:
        error = _(u'Video locator is required.')
    elif 'transcript-file' not in files:
        error = _(u'A transcript file is required.')
    elif os.path.splitext(files['transcript-file'].name)[1][1:] != Transcript.SRT:
        error = _(u'This transcript file type is not supported.')
    elif 'edx_video_id' not in data:
        error = _(u'Video ID is required.')

    if not error:
        error, video = validate_video_module(request, video_locator)
        if not error:
            validated_data.update({
                'video': video,
                'edx_video_id': clean_video_id(edx_video_id) or clean_video_id(video.edx_video_id),
                'transcript_file': files['transcript-file']
            })

    return error, validated_data


@login_required
def upload_transcripts(request):
    """
    Upload transcripts for current module.

    returns: response dict::

        status: 'Success' and HTTP 200 or 'Error' and HTTP 400.
        subs: Value of uploaded and saved html5 sub field in video item.
    """
    error, validated_data = validate_transcript_upload_data(request)
    if error:
        response = JsonResponse({'status': error}, status=400)
    else:
        video = validated_data['video']
        edx_video_id = validated_data['edx_video_id']
        transcript_file = validated_data['transcript_file']
        # check if we need to create an external VAL video to associate the transcript
        # and save its ID on the video component.
        if not edx_video_id:
            edx_video_id = create_external_video(display_name=u'external video')
            video.edx_video_id = edx_video_id
            video.save_with_metadata(request.user)

        response = JsonResponse({'edx_video_id': edx_video_id, 'status': 'Success'}, status=200)

        try:
            # Convert 'srt' transcript into the 'sjson' and upload it to
            # configured transcript storage. For example, S3.
            sjson_subs = Transcript.convert(
                content=transcript_file.read().decode('utf-8'),
                input_format=Transcript.SRT,
                output_format=Transcript.SJSON
            ).encode()
            transcript_created = create_or_update_video_transcript(
                video_id=edx_video_id,
                language_code=u'en',
                metadata={
                    'provider': TranscriptProvider.CUSTOM,
                    'file_format': Transcript.SJSON,
                    'language_code': u'en'
                },
                file_data=ContentFile(sjson_subs),
            )

            if transcript_created is None:
                response = JsonResponse({'status': 'Invalid Video ID'}, status=400)

        except (TranscriptsGenerationException, UnicodeDecodeError):

            response = JsonResponse({
                'status': _(u'There is a problem with this transcript file. Try to upload a different file.')
            }, status=400)

    return response


@login_required
def download_transcripts(request):
    """
    Passes to user requested transcripts file.

    Raises Http404 if unsuccessful.
    """
    error, video = validate_video_module(request, locator=request.GET.get('locator'))
    if error:
        raise Http404

    try:
        content, filename, mimetype = get_transcript(video, lang=u'en')
    except NotFoundError:
        raise Http404

    # Construct an HTTP response
    response = HttpResponse(content, content_type=mimetype)
    response['Content-Disposition'] = u'attachment; filename="{filename}"'.format(filename=filename)
    return response


@login_required
def check_transcripts(request):
    """
    Check state of transcripts availability.

    request.GET['data'] has key `videos`, which can contain any of the following::

        [
            {u'type': u'youtube', u'video': u'OEoXaMPEzfM', u'mode': u'youtube'},
            {u'type': u'html5',    u'video': u'video1',             u'mode': u'mp4'}
            {u'type': u'html5',    u'video': u'video2',             u'mode': u'webm'}
        ]
        `type` is youtube or html5
        `video` is html5 or youtube video_id
        `mode` is youtube, ,p4 or webm

    Returns transcripts_presence dict::

        html5_local: list of html5 ids, if subtitles exist locally for them;
        is_youtube_mode: bool, if we have youtube_id, and as youtube mode is of higher priority, reflect this with flag;
        youtube_local: bool, if youtube transcripts exist locally;
        youtube_server: bool, if youtube transcripts exist on server;
        youtube_diff: bool, if youtube transcripts exist on youtube server, and are different from local youtube ones;
        current_item_subs: string, value of item.sub field;
        status: string, 'Error' or 'Success';
        subs: string, new value of item.sub field, that should be set in module;
        command: string, action to front-end what to do and what to show to user.
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

    try:
        __, videos, item = _validate_transcripts_data(request)
    except TranscriptsRequestValidationException as e:
        return error_response(transcripts_presence, text_type(e))

    transcripts_presence['status'] = 'Success'

    try:
        edx_video_id = clean_video_id(videos.get('edx_video_id'))
        get_transcript_from_val(edx_video_id=edx_video_id, lang=u'en')
        command = 'found'
    except NotFoundError:
        filename = 'subs_{0}.srt.sjson'.format(item.sub)
        content_location = StaticContent.compute_location(item.location.course_key, filename)
        try:
            local_transcripts = contentstore().find(content_location).data.decode('utf-8')
            transcripts_presence['current_item_subs'] = item.sub
        except NotFoundError:
            pass

        # Check for youtube transcripts presence
        youtube_id = videos.get('youtube', None)
        if youtube_id:
            transcripts_presence['is_youtube_mode'] = True

            # youtube local
            filename = 'subs_{0}.srt.sjson'.format(youtube_id)
            content_location = StaticContent.compute_location(item.location.course_key, filename)
            try:
                local_transcripts = contentstore().find(content_location).data.decode('utf-8')
                transcripts_presence['youtube_local'] = True
            except NotFoundError:
                log.debug(u"Can't find transcripts in storage for youtube id: %s", youtube_id)

            # youtube server
            youtube_text_api = copy.deepcopy(settings.YOUTUBE['TEXT_API'])
            youtube_text_api['params']['v'] = youtube_id
            youtube_transcript_name = youtube_video_transcript_name(youtube_text_api)
            if youtube_transcript_name:
                youtube_text_api['params']['name'] = youtube_transcript_name
            youtube_response = requests.get('http://' + youtube_text_api['url'], params=youtube_text_api['params'])

            if youtube_response.status_code == 200 and youtube_response.text:
                transcripts_presence['youtube_server'] = True
            #check youtube local and server transcripts for equality
            if transcripts_presence['youtube_server'] and transcripts_presence['youtube_local']:
                try:
                    youtube_server_subs = get_transcripts_from_youtube(
                        youtube_id,
                        settings,
                        item.runtime.service(item, "i18n")
                    )
                    if json.loads(local_transcripts) == youtube_server_subs:  # check transcripts for equality
                        transcripts_presence['youtube_diff'] = False
                except GetTranscriptsFromYouTubeException:
                    pass

        # Check for html5 local transcripts presence
        html5_subs = []
        for html5_id in videos['html5']:
            filename = 'subs_{0}.srt.sjson'.format(html5_id)
            content_location = StaticContent.compute_location(item.location.course_key, filename)
            try:
                html5_subs.append(contentstore().find(content_location).data)
                transcripts_presence['html5_local'].append(html5_id)
            except NotFoundError:
                log.debug(u"Can't find transcripts in storage for non-youtube video_id: %s", html5_id)
            if len(html5_subs) == 2:  # check html5 transcripts for equality
                transcripts_presence['html5_equal'] = (
                    json.loads(html5_subs[0].decode('utf-8')) == json.loads(html5_subs[1].decode('utf-8'))
                )

        command, __ = _transcripts_logic(transcripts_presence, videos)

    transcripts_presence.update({'command': command})
    return JsonResponse(transcripts_presence)


def _transcripts_logic(transcripts_presence, videos):
    """
    By `transcripts_presence` content, figure what show to user:

    returns: `command` and `subs`.

    `command`: string,  action to front-end what to do and what show to user.
    `subs`: string, new value of item.sub field, that should be set in module.

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
        subs = videos['youtube']
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
                subs = transcripts_presence['html5_local'][0]
        else:  # html5 source have no subtitles
            # check if item sub has subtitles
            if transcripts_presence['current_item_subs'] and not transcripts_presence['is_youtube_mode']:
                log.debug(u"Command is use existing %s subs", transcripts_presence['current_item_subs'])
                command = 'use_existing'
            else:
                command = 'not_found'
    log.debug(
        u"Resulted command: %s, current transcripts: %s, youtube mode: %s",
        command,
        transcripts_presence['current_item_subs'],
        transcripts_presence['is_youtube_mode']
    )
    return command, subs


def _validate_transcripts_data(request):
    """
    Validates, that request contains all proper data for transcripts processing.

    Returns tuple of 3 elements::

        data: dict, loaded json from request,
        videos: parsed `data` to useful format,
        item:  video item from storage

    Raises `TranscriptsRequestValidationException` if validation is unsuccessful
    or `PermissionDenied` if user has no access.
    """
    data = json.loads(request.GET.get('data', '{}'))
    if not data:
        raise TranscriptsRequestValidationException(_('Incoming video data is empty.'))

    try:
        item = _get_item(request, data)
    except (InvalidKeyError, ItemNotFoundError):
        raise TranscriptsRequestValidationException(_("Can't find item by locator."))

    if item.category != 'video':
        raise TranscriptsRequestValidationException(_('Transcripts are supported only for "video" modules.'))

    # parse data form request.GET.['data']['video'] to useful format
    videos = {'youtube': '', 'html5': {}}
    for video_data in data.get('videos'):
        if video_data['type'] == 'youtube':
            videos['youtube'] = video_data['video']
        elif video_data['type'] == 'edx_video_id':
            if clean_video_id(video_data['video']):
                videos['edx_video_id'] = video_data['video']
        else:  # do not add same html5 videos
            if videos['html5'].get('video') != video_data['video']:
                videos['html5'][video_data['video']] = video_data['mode']

    return data, videos, item


def validate_transcripts_request(request, include_yt=False, include_html5=False):
    """
    Validates transcript handler's request.

    NOTE: This is one central validation flow for `choose_transcripts`,
    `check_transcripts` and `replace_transcripts` handlers.

    Returns:
        A tuple containing:
            1. An error message in case of validation failure.
            2. validated video data
    """
    error = None
    validated_data = {'video': None, 'youtube': '', 'html5': {}}
    # Loads the request data
    data = json.loads(request.GET.get('data', '{}'))
    if not data:
        error = _(u'Incoming video data is empty.')
    else:
        error, video = validate_video_module(request, locator=data.get('locator'))
        if not error:
            validated_data.update({'video': video})

    videos = data.get('videos', [])
    if include_yt:
        validated_data.update({
            video['type']: video['video']
            for video in videos
            if video['type'] == 'youtube'
        })

    if include_html5:
        validated_data['chosen_html5_id'] = data.get('html5_id')
        validated_data['html5'] = {
            video['video']: video['mode']
            for video in videos
            if video['type'] != 'youtube'
        }

    return error, validated_data


@login_required
def choose_transcripts(request):
    """
    Create/Update edx transcript in DS with chosen html5 subtitles from contentstore.

    Returns:
        status `Success` and resulted `edx_video_id` value
        Or error in case of validation failures.
    """
    error, validated_data = validate_transcripts_request(request, include_html5=True)
    if error:
        response = error_response({}, error)
    else:
        # 1. Retrieve transcript file for `chosen_html5_id` from contentstore.
        try:
            video = validated_data['video']
            chosen_html5_id = validated_data['chosen_html5_id']
            input_format, __, transcript_content = get_transcript_for_video(
                video.location,
                subs_id=chosen_html5_id,
                file_name=chosen_html5_id,
                language=u'en'
            )
        except NotFoundError:
            return error_response({}, _('No such transcript.'))

        # 2. Link a video to video component if its not already linked to one.
        edx_video_id = link_video_to_component(video, request.user)

        # 3. Upload the retrieved transcript to DS for the linked video ID.
        success = save_video_transcript(edx_video_id, input_format, transcript_content, language_code=u'en')
        if success:
            response = JsonResponse({'edx_video_id': edx_video_id, 'status': 'Success'}, status=200)
        else:
            response = error_response({}, _('There is a problem with the chosen transcript file.'))

    return response


@login_required
def rename_transcripts(request):
    """
    Copies existing transcript on video component's `sub`(from contentstore) into the
    DS for a video.

    Returns:
        status `Success` and resulted `edx_video_id` value
        Or error in case of validation failures.
    """
    error, validated_data = validate_transcripts_request(request)
    if error:
        response = error_response({}, error)
    else:
        # 1. Retrieve transcript file for `video.sub` from contentstore.
        try:
            video = validated_data['video']
            input_format, __, transcript_content = get_transcript_for_video(
                video.location,
                subs_id=video.sub,
                file_name=video.sub,
                language=u'en'
            )
        except NotFoundError:
            return error_response({}, _('No such transcript.'))

        # 2. Link a video to video component if its not already linked to one.
        edx_video_id = link_video_to_component(video, request.user)

        # 3. Upload the retrieved transcript to DS for the linked video ID.
        success = save_video_transcript(edx_video_id, input_format, transcript_content, language_code=u'en')
        if success:
            response = JsonResponse({'edx_video_id': edx_video_id, 'status': 'Success'}, status=200)
        else:
            response = error_response(
                {}, _('There is a problem with the existing transcript file. Please upload a different file.')
            )

    return response


@login_required
def replace_transcripts(request):
    """
    Downloads subtitles from youtube and replaces edx transcripts in DS with youtube ones.

    Returns:
        status `Success` and resulted `edx_video_id` value
        Or error on validation failures.
    """
    error, validated_data = validate_transcripts_request(request, include_yt=True)
    youtube_id = validated_data['youtube']
    if error:
        response = error_response({}, error)
    elif not youtube_id:
        response = error_response({}, _(u'YouTube ID is required.'))
    else:
        # 1. Download transcript from YouTube.
        try:
            video = validated_data['video']
            transcript_content = download_youtube_subs(youtube_id, video, settings)
        except GetTranscriptsFromYouTubeException as e:
            return error_response({}, text_type(e))

        # 2. Link a video to video component if its not already linked to one.
        edx_video_id = link_video_to_component(video, request.user)

        # 3. Upload YT transcript to DS for the linked video ID.
        success = save_video_transcript(edx_video_id, Transcript.SJSON, transcript_content, language_code=u'en')
        if success:
            response = JsonResponse({'edx_video_id': edx_video_id, 'status': 'Success'}, status=200)
        else:
            response = error_response({}, _('There is a problem with the YouTube transcript file.'))

    return response


def _get_item(request, data):
    """
    Obtains from 'data' the locator for an item.
    Next, gets that item from the modulestore (allowing any errors to raise up).
    Finally, verifies that the user has access to the item.

    Returns the item.
    """
    usage_key = UsageKey.from_string(data.get('locator'))
    # This is placed before has_course_author_access() to validate the location,
    # because has_course_author_access() raises  r if location is invalid.
    item = modulestore().get_item(usage_key)

    # use the item's course_key, because the usage_key might not have the run
    if not has_course_author_access(request.user, item.location.course_key):
        raise PermissionDenied()

    return item
