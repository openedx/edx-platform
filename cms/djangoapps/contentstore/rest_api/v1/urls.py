""" Contenstore API v1 URLs. """

from django.conf import settings
from django.urls import re_path, path

from openedx.core.constants import COURSE_ID_PATTERN

from .views import (
    CourseDetailsView,
    CourseTeamView,
    CourseGradingView,
    CourseRerunView,
    CourseSettingsView,
    HomePageView,
    ProctoredExamSettingsView,
    ProctoringErrorsView,
    xblock,
    assets,
    videos,
    transcripts,
    HelpUrlsView,
)

app_name = 'v1'

VIDEO_ID_PATTERN = r'(?P<edx_video_id>[-\w]+)'

urlpatterns = [
    path(
        'home',
        HomePageView.as_view(),
        name="home"
    ),
    re_path(
        fr'^proctored_exam_settings/{COURSE_ID_PATTERN}$',
        ProctoredExamSettingsView.as_view(),
        name="proctored_exam_settings"
    ),
    re_path(
        fr'^proctoring_errors/{COURSE_ID_PATTERN}$',
        ProctoringErrorsView.as_view(),
        name="proctoring_errors"
    ),
    re_path(
        fr'^course_settings/{COURSE_ID_PATTERN}$',
        CourseSettingsView.as_view(),
        name="course_settings"
    ),
    re_path(
        fr'^course_details/{COURSE_ID_PATTERN}$',
        CourseDetailsView.as_view(),
        name="course_details"
    ),
    re_path(
        fr'^course_team/{COURSE_ID_PATTERN}$',
        CourseTeamView.as_view(),
        name="course_team"
    ),
    re_path(
        fr'^course_grading/{COURSE_ID_PATTERN}$',
        CourseGradingView.as_view(),
        name="course_grading"
    ),
    path(
        'help_urls',
        HelpUrlsView.as_view(),
        name="help_urls"
    ),
    re_path(
        fr'^course_rerun/{COURSE_ID_PATTERN}$',
        CourseRerunView.as_view(),
        name="course_rerun"
    ),

    # CMS API
    re_path(
        fr'^file_assets/{settings.COURSE_ID_PATTERN}/$',
        assets.AssetsCreateRetrieveView.as_view(), name='cms_api_create_retrieve_assets'
    ),
    re_path(
        fr'^file_assets/{settings.COURSE_ID_PATTERN}/{settings.ASSET_KEY_PATTERN}$',
        assets.AssetsUpdateDestroyView.as_view(), name='cms_api_update_destroy_assets'
    ),
    re_path(
        fr'^videos/encodings/{settings.COURSE_ID_PATTERN}$',
        videos.VideoEncodingsDownloadView.as_view(), name='cms_api_videos_encodings'
    ),
    path(
        'videos/features/',
        videos.VideoFeaturesView.as_view(), name='cms_api_videos_features'
    ),
    re_path(
        fr'^videos/images/{settings.COURSE_ID_PATTERN}/{VIDEO_ID_PATTERN}$',
        videos.VideoImagesView.as_view(), name='cms_api_videos_images'
    ),
    re_path(
        fr'^videos/uploads/{settings.COURSE_ID_PATTERN}/$',
        videos.VideosCreateUploadView.as_view(), name='cms_api_create_videos_upload'
    ),
    re_path(
        fr'^videos/uploads/{settings.COURSE_ID_PATTERN}/{VIDEO_ID_PATTERN}$',
        videos.VideosUploadsView.as_view(), name='cms_api_videos_uploads'
    ),
    re_path(
        fr'^video_transcripts/{settings.COURSE_ID_PATTERN}$',
        transcripts.TranscriptView.as_view(), name='cms_api_video_transcripts'
    ),
    re_path(
        fr'^xblock/{settings.COURSE_ID_PATTERN}/$',
        xblock.XblockCreateView.as_view(), name='cms_api_create_xblock'
    ),
    re_path(
        fr'^xblock/{settings.COURSE_ID_PATTERN}/{settings.USAGE_KEY_PATTERN}$',
        xblock.XblockView.as_view(), name='cms_api_xblock'
    ),
]
