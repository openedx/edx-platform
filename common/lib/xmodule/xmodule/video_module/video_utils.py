# -*- coding: utf-8 -*-
"""
Module contains utils specific for video_module but not for transcripts.
"""
import json
from collections import OrderedDict
import logging
import urllib
import requests
from urllib import urlencode
from urlparse import parse_qs, urlsplit, urlunsplit

from django.conf import settings

from requests.exceptions import RequestException

log = logging.getLogger(__name__)


def create_youtube_string(module):
    """
    Create a string of Youtube IDs from `module`'s metadata
    attributes. Only writes a speed if an ID is present in the
    module.  Necessary for backwards compatibility with XML-based
    courses.
    """
    youtube_ids = [
        module.youtube_id_0_75,
        module.youtube_id_1_0,
        module.youtube_id_1_25,
        module.youtube_id_1_5
    ]
    youtube_speeds = ['0.75', '1.00', '1.25', '1.50']
    return ','.join([
        ':'.join(pair)
        for pair
        in zip(youtube_speeds, youtube_ids)
        if pair[1]
    ])


# def get_video_from_cdn(cdn_base_url, original_video_url, cdn_branding_logo_url):
# Not sure if this third variable is necessary...
def get_video_from_cdn(cdn_base_url, original_video_url):
    """
    Get video URL from CDN.

    `original_video_url` is the existing video url.
    Currently `cdn_base_url` equals 'http://api.xuetangx.com/edx/video?s3_url='
    Example of CDN outcome:
        {
            "sources":
                [
                    "http://cm12.c110.play.bokecc.com/flvs/ca/QxcVl/u39EQbA0Ra-20.mp4",
                    "http://bm1.42.play.bokecc.com/flvs/ca/QxcVl/u39EQbA0Ra-20.mp4"
                ],
            "s3_url": "http://s3.amazonaws.com/BESTech/CS169/download/CS169_v13_w5l2s3.mp4",
        }
    where `s3_url` is requested original video url and `sources` is the list of
    alternative links.
    """

    if not cdn_base_url:
        return None

    request_url = cdn_base_url + urllib.quote(original_video_url)

    try:
        cdn_response = requests.get(request_url, timeout=0.5)
    except RequestException as err:
        log.info("Request timed out to CDN server: %s", request_url, exc_info=True)
        return None

    if cdn_response.status_code == 200:
        cdn_content = json.loads(cdn_response.content)
        return cdn_content['sources'][0]
    else:
        return None


def get_poster(video):
    """
    Generate poster metadata.

    youtube_streams is string that contains '1.00:youtube_id'

    Poster metadata is dict of youtube url for image thumbnail and edx logo
    """
    if not video.bumper.get("enabled"):
        return

    poster = OrderedDict({"url": "", "type": ""})

    if video.youtube_streams:
        youtube_id = video.youtube_streams.split('1.00:')[1].split(',')[0]
        poster["url"] = settings.YOUTUBE['IMAGE_API'].format(youtube_id=youtube_id)
        poster["type"] = "youtube"
    else:
        poster["url"] = "https://www.edx.org/sites/default/files/theme/edx-logo-header.png"
        poster["type"] = "html5"

    return poster


def set_query_parameter(url, param_name, param_value):
    """
    Given a URL, set or replace a query parameter and return the
    modified URL.
    """
    scheme, netloc, path, query_string, fragment = urlsplit(url)
    query_params = parse_qs(query_string)
    query_params[param_name] = [param_value]
    new_query_string = urlencode(query_params, doseq=True)

    return urlunsplit((scheme, netloc, path, new_query_string, fragment))
