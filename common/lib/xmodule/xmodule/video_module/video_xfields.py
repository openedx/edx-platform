"""
XFields for video module.
"""
import datetime

from xblock.fields import Scope, String, Float, Boolean, List, Dict

from xmodule.fields import RelativeTime


class VideoFields(object):
    """Fields for `VideoModule` and `VideoDescriptor`."""
    display_name = String(
        display_name="Display Name", help="Display name for this module.",
        default="Video",
        scope=Scope.settings
    )
    saved_video_position = RelativeTime(
        help="Current position in the video",
        scope=Scope.user_state,
        default=datetime.timedelta(seconds=0)
    )
    # TODO: This should be moved to Scope.content, but this will
    # require data migration to support the old video module.
    youtube_id_1_0 = String(
        help="This is the Youtube ID reference for the normal speed video.",
        display_name="Youtube ID",
        scope=Scope.settings,
        default="OEoXaMPEzfM"
    )
    youtube_id_0_75 = String(
        help="Optional, for older browsers: the Youtube ID for the .75x speed video.",
        display_name="Youtube ID for .75x speed",
        scope=Scope.settings,
        default=""
    )
    youtube_id_1_25 = String(
        help="Optional, for older browsers: the Youtube ID for the 1.25x speed video.",
        display_name="Youtube ID for 1.25x speed",
        scope=Scope.settings,
        default=""
    )
    youtube_id_1_5 = String(
        help="Optional, for older browsers: the Youtube ID for the 1.5x speed video.",
        display_name="Youtube ID for 1.5x speed",
        scope=Scope.settings,
        default=""
    )
    start_time = RelativeTime(  # datetime.timedelta object
        help="Start time for the video (HH:MM:SS). Max value is 23:59:59.",
        display_name="Start Time",
        scope=Scope.settings,
        default=datetime.timedelta(seconds=0)
    )
    end_time = RelativeTime(  # datetime.timedelta object
        help="End time for the video (HH:MM:SS). Max value is 23:59:59.",
        display_name="End Time",
        scope=Scope.settings,
        default=datetime.timedelta(seconds=0)
    )
    #front-end code of video player checks logical validity of (start_time, end_time) pair.

    # `source` is deprecated field and should not be used in future.
    # `download_video` is used instead.
    source = String(
        help="The external URL to download the video.",
        display_name="Download Video",
        scope=Scope.settings,
        default=""
    )
    download_video = Boolean(
        help="Show a link beneath the video to allow students to download the video. Note: You must add at least one video source below.",
        display_name="Video Download Allowed",
        scope=Scope.settings,
        default=False
    )
    html5_sources = List(
        help="A list of filenames to be used with HTML5 video. The first supported filetype will be displayed.",
        display_name="Video Sources",
        scope=Scope.settings,
    )
    track = String(
        help="The external URL to download the timed transcript track. This appears as a link beneath the video.",
        display_name="Download Transcript",
        scope=Scope.settings,
        default=''
    )
    download_track = Boolean(
        help="Show a link beneath the video to allow students to download the transcript. Note: You must add a link to the HTML5 Transcript field above.",
        display_name="Transcript Download Allowed",
        scope=Scope.settings,
        default=False
    )
    sub = String(
        help="The name of the timed transcript track (for non-Youtube videos).",
        display_name="Transcript (primary)",
        scope=Scope.settings,
        default=""
    )
    show_captions = Boolean(
        help="This controls whether or not captions are shown by default.",
        display_name="Transcript Display",
        scope=Scope.settings,
        default=True
    )
    # Data format: {'de': 'german_translation', 'uk': 'ukrainian_translation'}
    transcripts = Dict(
        help="Add additional transcripts in other languages",
        display_name="Transcript Translations",
        scope=Scope.settings,
        default={}
    )
    transcript_language = String(
        help="Preferred language for transcript",
        display_name="Preferred language for transcript",
        scope=Scope.preferences,
        default="en"
    )
    transcript_download_format = String(
        help="Transcript file format to download by user.",
        scope=Scope.preferences,
        values=[
            {"display_name": "SubRip (.srt) file", "value": "srt"},
            {"display_name": "Text (.txt) file", "value": "txt"}
        ],
        default='srt',
    )
    speed = Float(
        help="The last speed that was explicitly set by user for the video.",
        scope=Scope.user_state,
    )
    global_speed = Float(
        help="Default speed in cases when speed wasn't explicitly for specific video",
        scope=Scope.preferences,
        default=1.0
    )
    youtube_is_available = Boolean(
        help="The availaibility of YouTube API for the user",
        scope=Scope.user_info,
        default=True
    )
