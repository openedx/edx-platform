# -*- coding: utf-8 -*-
"""
Module contains utils specific for video_module but not for transcripts.
"""
import json
import logging
import urllib
import requests
import urlparse

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
def get_video_from_cdn(cdn_base_url, original_video_url, **kwargs):
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

    kwargs may contain:
        play_video_local (bool): whether to play video from locally hosted server, for exaple Nginx.

        How-to:
            1. Download all videos from the course.
            2. Install and setup Nginx. Actually even w/o additional modules for video streaming nginx will work. Setup nginx: if, for example, root entry point is /Users/kry/repos/edx/videos, then, in default nginx config, set

                    location / {
                       root   /Users/kry/repos/edx/videos;
                       index  index.html index.htm;
                       autoindex on;
                    }

            4. If Open edX video has url:
                    https://s3.amazonaws.com/edx-course-videos/edx-intro/video.mp4,
                then create subfolders
                    edx-course-videos/edx-intro,
                and copy video to the inner, so path to video on local drive will be:
                    /Users/kry/repos/edx/videos/edx-course-videos/edx-intro/video.mp4
            5. To enable feature add
                    "PLAY_VIDEO_LOCAL": "http://localhost:8080/folder_with_video/"
               to FEATURES dict in lms and cms .env.json files,
               where http://localhost:8080 is url for Nginx site with hosted videos
    """
    if kwargs.get('play_video_local'):
        scheme, netloc = kwargs.get('play_video_local').rstrip('/').split('://')
        parsed = urlparse.urlparse(original_video_url)
        replaced = parsed._replace(netloc=netloc, scheme=scheme)
        return replaced.geturl()

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
