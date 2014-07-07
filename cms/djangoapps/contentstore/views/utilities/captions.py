"""
Views related to operations on course objects
"""
import json
import logging
import os

from django_future.csrf import ensure_csrf_cookie
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseBadRequest, HttpResponseNotFound
from django.utils.translation import ugettext as _
from edxmako.shortcuts import render_to_response

from opaque_keys import InvalidKeyError
from util.json_request import JsonResponse
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError, InsufficientSpecificationError
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.keys import UsageKey
from xmodule.video_module.transcripts_utils import (
                                    GetTranscriptsFromYouTubeException,
                                    TranscriptsRequestValidationException,
                                    download_youtube_subs)

from ..transcripts_ajax import get_transcripts_presence
from ..course import _get_course_module


log = logging.getLogger(__name__)

__all__ = ['utility_captions_handler']


# pylint: disable=unused-argument
@login_required
def utility_captions_handler(request, course_key_string):
    """
    The restful handler for captions requests in the utilities area.
    It provides the list of course videos as well as their status. It also lets
    the user update the captions by pulling the latest version from YouTube.

    GET
        json: get the status of the captions of a given video
        html: return page containing a list of videos in the course
    POST
        json: update the captions of a given video by copying the version of the captions hosted in youtube.
    """
    course_key = CourseKey.from_string(course_key_string)
    response_format = request.REQUEST.get('format', 'html')
    if response_format == 'json' or 'application/json' in request.META.get('HTTP_ACCEPT', 'application/json'):
        if request.method == 'POST':  # update
            try:
                locations = _validate_captions_data_update(request, course_key)
            except TranscriptsRequestValidationException as e:
                return error_response(e.message)
            return json_update_videos(request, locations)
        elif request.method == 'GET':  # get status
            try:
                data, item = _validate_captions_data_get(request, course_key)
            except TranscriptsRequestValidationException as e:
                return error_response(e.message)
            return json_get_video_status(data, item)
        else:
            return HttpResponseBadRequest()
    elif request.method == 'GET':  # assume html
        return captions_index(request, course_key)
    else:
        return HttpResponseNotFound()


@login_required
@ensure_csrf_cookie
def json_update_videos(request, locations):
    """
    Updates the captions of a given list of videos and returns the status of the
    videos in json format

    request: the incoming request to update the videos
    locations: list of locations of videos to be updated
    """
    results = []
    for key_string in locations:
        key = UsageKey.from_string(key_string)
        try:
            #update transcripts
            item = modulestore().get_item(key)
            download_youtube_subs({1.0: item.youtube_id_1_0}, item, settings)

            #get new status
            videos = {'youtube': item.youtube_id_1_0}
            html5 = {}
            for url in item.html5_sources:
                name = os.path.splitext(url.split('/')[-1])[0]
                html5[name] = 'html5'
            videos['html5'] = html5
            captions_dict = get_transcripts_presence(videos, item)
            captions_dict.update({'location': key_string})
            results.append(captions_dict)

        except GetTranscriptsFromYouTubeException as e:
            log.debug(e)
            results.append({'location': key_string, 'command': e})

    return JsonResponse(results)


@login_required
@ensure_csrf_cookie
def captions_index(request, course_key):
    """
    Display a list of course videos as well as their status (up to date, or out of date)

    org, course, name: Attributes of the Location for the item to edit
    """
    course = _get_course_module(
        course_key,
        request.user,
        depth=2,
    )

    return render_to_response('captions.html',
        {
            'videos': get_videos(course),
            'context_course': course,
        }
    )


def error_response(message, response=None, status_code=400):
    """
    Simplify similar actions: log message and return JsonResponse with message included in response.

    By default return 400 (Bad Request) Response.
    """
    if response is None:
        response = {}
    log.debug(message)
    response['message'] = message
    return JsonResponse(response, status_code)


def _validate_captions_data_get(request, course_key):
    """
    Happens on 'GET'. Validates, that request contains all proper data for transcripts processing.

    Returns touple of two elements:
        data: dict, loaded json from request,
        item: video item from storage

    Raises `TranscriptsRequestValidationException` if validation is unsuccessful
    or `PermissionDenied` if user has no access.
    """
    try:
        data = json.loads(request.GET.get('video', '{}'))
    except ValueError:
        raise TranscriptsRequestValidationException(_("Invalid location."))

    if not data:
        raise TranscriptsRequestValidationException(_('Incoming video data is empty.'))

    location = data.get('location')
    item = _validate_location(location, course_key)
    return data, item


def _validate_captions_data_update(request, course_key):
    """
    Happens on 'POST'. Validates, that request contains all proper data for transcripts processing.

    Returns data: dict, loaded json from request

    Raises `TranscriptsRequestValidationException` if validation is unsuccessful
    or `PermissionDenied` if user has no access.
    """
    try:
        data = json.loads(request.POST.get('update_array', '[]'))
    except ValueError:
        raise TranscriptsRequestValidationException(_("Invalid locations."))

    if not data:
        raise TranscriptsRequestValidationException(_('Incoming update_array data is empty.'))

    for location in data:
        _validate_location(location, course_key)
    return data


def _validate_location(location, course_key):
    try:
        location = UsageKey.from_string(location)
        item = modulestore().get_item(location)
    except (ItemNotFoundError, InvalidKeyError, InsufficientSpecificationError):
        raise TranscriptsRequestValidationException(_("Can't find item by locator."))

    if item.category != 'video':
        raise TranscriptsRequestValidationException(_('Transcripts are supported only for "video" modules.'))
    return item


def json_get_video_status(video_meta, item):
    """
    Fetches the status of a given video

    Returns: json response which includes a detailed status of the video captions
    """

    videos = {'youtube': item.youtube_id_1_0}
    html5 = {}
    for url in item.html5_sources:
        name = os.path.splitext(url.split('/')[-1])[0]
        html5[name] = 'html5'
    videos['html5'] = html5
    transcripts_presence = get_transcripts_presence(videos, item)
    video_meta.update(transcripts_presence)
    return JsonResponse(video_meta)


def get_videos(course):
    """
    Fetches the list of course videos

    Returns: A list of tuples representing (name, location) of each video
    """
    video_list = []
    for section in course.get_children():
        for subsection in section.get_children():
            for unit in subsection.get_children():
                for component in unit.get_children():
                    if component.location.category == 'video':
                        video_list.append({'name': component.display_name_with_default, 'location': str(component.location)})
    return video_list
