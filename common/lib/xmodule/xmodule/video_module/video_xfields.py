"""
XFields for video module.
"""
import datetime

from xblock.fields import Scope, String, Float, Boolean, List, Dict

from xmodule.fields import RelativeTime

# Make '_' a no-op so we can scrape strings
_ = lambda text: text


class VideoFields(object):
    """Fields for `VideoModule` and `VideoDescriptor`."""
    display_name = String(
        help=_("The name students see. This name appears in the course ribbon and as a header for the video."),
        display_name=_("Component Display Name"),
        default="Video",
        scope=Scope.settings
    )

    saved_video_position = RelativeTime(
        help=_("Current position in the video."),
        scope=Scope.user_state,
        default=datetime.timedelta(seconds=0)
    )
    # TODO: This should be moved to Scope.content, but this will
    # require data migration to support the old video module.
    youtube_id_1_0 = String(
        help=_("Optional, for older browsers: the YouTube ID for the normal speed video."),
        display_name=_("YouTube ID"),
        scope=Scope.settings,
        default="OEoXaMPEzfM"
    )
    youtube_id_0_75 = String(
        help=_("Optional, for older browsers: the YouTube ID for the .75x speed video."),
        display_name=_("YouTube ID for .75x speed"),
        scope=Scope.settings,
        default=""
    )
    youtube_id_1_25 = String(
        help=_("Optional, for older browsers: the YouTube ID for the 1.25x speed video."),
        display_name=_("YouTube ID for 1.25x speed"),
        scope=Scope.settings,
        default=""
    )
    youtube_id_1_5 = String(
        help=_("Optional, for older browsers: the YouTube ID for the 1.5x speed video."),
        display_name=_("YouTube ID for 1.5x speed"),
        scope=Scope.settings,
        default=""
    )
    start_time = RelativeTime(  # datetime.timedelta object
        help=_("Time you want the video to start if you don't want the entire video to play. Formatted as HH:MM:SS. The maximum value is 23:59:59."),
        display_name=_("Video Start Time"),
        scope=Scope.settings,
        default=datetime.timedelta(seconds=0)
    )
    end_time = RelativeTime(  # datetime.timedelta object
        help=_("Time you want the video to stop if you don't want the entire video to play. Formatted as HH:MM:SS. The maximum value is 23:59:59."),
        display_name=_("Video Stop Time"),
        scope=Scope.settings,
        default=datetime.timedelta(seconds=0)
    )
    #front-end code of video player checks logical validity of (start_time, end_time) pair.

    # `source` is deprecated field and should not be used in future.
    # `download_video` is used instead.
    source = String(
        help=_("The external URL to download the video."),
        display_name=_("Download Video"),
        scope=Scope.settings,
        default=""
    )
    download_video = Boolean(
        help=_("Allow students to download versions of this video in different formats if they cannot use the edX video player or do not have access to YouTube. You must add at least one non-YouTube URL in the Video File URLs field."),
        display_name=_("Video Download Allowed"),
        scope=Scope.settings,
        default=False
    )
    html5_sources = List(
        help=_("The URL or URLs where you've posted non-YouTube versions of the video. Each URL must end in .mpeg, .mp4, .ogg, or .webm and cannot be a YouTube URL. (For browser compatibility, we strongly recommend .mp4 and .webm format.) Students will be able to view the first listed video that's compatible with the student's computer. To allow students to download these videos, set Video Download Allowed to True."),
        display_name=_("Video File URLs"),
        scope=Scope.settings,
    )
    track = String(
        help=_("By default, students can download an .srt or .txt transcript when you set Download Transcript Allowed to True. If you want to provide a downloadable transcript in a different format, we recommend that you upload a handout by using the Upload a Handout field. If this isn't possible, you can post a transcript file on the Files & Uploads page or on the Internet, and then add the URL for the transcript here. Students see a link to download that transcript below the video."),
        display_name=_("Downloadable Transcript URL"),
        scope=Scope.settings,
        default=''
    )
    download_track = Boolean(
        help=_("Allow students to download the timed transcript. A link to download the file appears below the video. By default, the transcript is an .srt or .txt file. If you want to provide the transcript for download in a different format, upload a file by using the Upload Handout field."),
        display_name=_("Download Transcript Allowed"),
        scope=Scope.settings,
        default=False
    )
    sub = String(
        help=_("The default transcript for the video, from the Default Timed Transcript field on the Basic tab. This transcript should be in English. You don't have to change this setting."),
        display_name=_("Default Timed Transcript"),
        scope=Scope.settings,
        default=""
    )
    show_captions = Boolean(
        help=_("Specify whether the transcripts appear with the video by default."),
        display_name=_("Show Transcript"),
        scope=Scope.settings,
        default=True
    )
    # Data format: {'de': 'german_translation', 'uk': 'ukrainian_translation'}
    transcripts = Dict(
        help=_("Add transcripts in different languages. Click below to specify a language and upload an .srt transcript file for that language."),
        display_name=_("Transcript Languages"),
        scope=Scope.settings,
        default={}
    )
    transcript_language = String(
        help=_("Preferred language for transcript."),
        display_name=_("Preferred language for transcript"),
        scope=Scope.preferences,
        default="en"
    )
    transcript_download_format = String(
        help=_("Transcript file format to download by user."),
        scope=Scope.preferences,
        values=[
            # Translators: This is a type of file used for captioning in the video player.
            {"display_name": _("SubRip (.srt) file"), "value": "srt"},
            {"display_name": _("Text (.txt) file"), "value": "txt"}
        ],
        default='srt',
    )
    speed = Float(
        help=_("The last speed that the user specified for the video."),
        scope=Scope.user_state,
    )
    global_speed = Float(
        help=_("The default speed for the video."),
        scope=Scope.preferences,
        default=1.0
    )
    youtube_is_available = Boolean(
        help=_("Specify whether YouTube is available for the user."),
        scope=Scope.user_info,
        default=True
    )

    handout = String(
        help=_("Upload a handout to accompany this video. Students can download the handout by clicking Download Handout under the video."),
        display_name=_("Upload Handout"),
        scope=Scope.settings,
    )
    video_link_transience = String(
        help=_("Enter the AWS access key, secret key and bucket name used for creating a transient video URLs in the following format: \"bucket_name\":\"access_key:secret_key\"."),
        display_name=_("Video Link Transience Credentials"),
        scope=Scope.settings
    )
