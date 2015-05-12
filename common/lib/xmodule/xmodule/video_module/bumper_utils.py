"""
Utils for video bumper
"""
import json
import pytz
import logging
from collections import OrderedDict

from datetime import datetime, timedelta
from django.conf import settings

try:
    import edxval.api as edxval_api
except ImportError:
    edxval_api = None

log = logging.getLogger(__name__)


def get_bumper_settings(video):
    """
    Get bumper settings from video instance.
    """
    return getattr(video, 'video_bumper', {})


def is_bumper_enabled(video):
    """
    Check if bumper enabled.

    - Feature flag ENABLE_VIDEO_BUMPER should be set to True
    - Do not show again button should not be clicked by user.
    - Current time minus periodicity must be greater that last time viewed
    - edxval_api should be presented

    Returns:
         bool.
    """
    date_last_view_bumper = getattr(video, 'date_last_view_bumper', None)
    utc_now = datetime.utcnow().replace(tzinfo=pytz.utc)
    periodicity = settings.FEATURES.get('SHOW_BUMPER_PERIODICITY', 0)
    has_viewed = any([
        getattr(video, 'do_not_show_again_bumper'),
        (date_last_view_bumper and date_last_view_bumper + timedelta(seconds=periodicity) > utc_now)
    ])
    return bool(
        settings.FEATURES.get('ENABLE_VIDEO_BUMPER') and
        get_bumper_settings(video) and
        edxval_api and
        not has_viewed
    )


def bumperize(video):
    """
    Populate video with bumper settings, if they are presented.
    """
    video.bumper = {
        'enabled': False,
        'edx_video_id': "",
        'transcripts': {},
        'metadata': None,
    }

    if not is_bumper_enabled(video):
        return

    bumper_settings = get_bumper_settings(video)

    try:
        video.bumper['edx_video_id'] = bumper_settings['video_id']
        video.bumper['transcripts'] = bumper_settings['transcripts']
    except (TypeError, KeyError):
        log.warning(
            "Could not retrieve video bumper information from course settings"
        )
        return

    sources = get_bumper_sources(video)
    if not sources:
        return

    video.bumper.update({
        'metadata': bumper_metadata(video, sources),
        'enabled': True,  # Video poster needs this.
    })


def get_bumper_sources(video):
    """
    Get bumper sources from edxval.

    Returns list of sources.
    """
    try:
        val_profiles = ["desktop_webm", "desktop_mp4"]
        val_video_urls = edxval_api.get_urls_for_profiles(video.bumper['edx_video_id'], val_profiles)
        bumper_sources = filter(None, [val_video_urls[p] for p in val_profiles])
    except edxval_api.ValInternalError:
        # if no bumper sources, nothing will be showed
        log.warning(
            "Could not retrieve information from VAL for Bumper edx Video ID: %s.", video.bumper['edx_video_id']
        )
        return []

    return bumper_sources


def bumper_metadata(video, sources):
    """
    Generate bumper metadata.
    """
    unused_track_url, bumper_transcript_language, bumper_languages = video.get_transcripts_for_student(
        video.bumper['transcripts'], bumper=True
    )

    metadata = OrderedDict({
        'sources': sources,
        'showCaptions': json.dumps(bool(video.bumper['transcripts'])),  # TODO: clarify - send it, Anton?
        'transcriptLanguage': bumper_transcript_language,
        'transcriptLanguages': bumper_languages,
        'transcriptTranslationUrl': video.runtime.handler_url(video, 'transcript', 'translation_bumper').rstrip('/?'),
        'transcriptAvailableTranslationsUrl': video.runtime.handler_url(
            video, 'transcript', 'available_translations_bumper'
        ).rstrip('/?'),
    })

    return metadata
