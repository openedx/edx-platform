""" Contenstore API v1 URLs. """

from django.urls import re_path
from django.conf import settings

from openedx.core.constants import COURSE_ID_PATTERN

from .views import (
    CourseDetailsView,
    CourseGradingView,
    CourseSettingsView,
    ProctoredExamSettingsView,
    ProctoringErrorsView,
    xblock,
    assets,
    videos,
)

app_name = 'v1'

VIDEO_ID_PATTERN = r'(?:/(?P<edx_video_id>[-\w]+))'

urlpatterns = [
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
        fr'^course_grading/{COURSE_ID_PATTERN}$',
        CourseGradingView.as_view(),
        name="course_grading"
    ),
    re_path(
        fr'^xblock/{settings.COURSE_ID_PATTERN}/{settings.USAGE_KEY_PATTERN}?$',
        xblock.XblockView.as_view(), name='studio_content'
    ),
    re_path(
        fr'^file_assets/{settings.COURSE_ID_PATTERN}/{settings.ASSET_KEY_PATTERN}?$',
        assets.AssetsView.as_view(), name='studio_content_assets'
    ),
    re_path(
        fr'^videos/uploads/{settings.COURSE_ID_PATTERN}/{VIDEO_ID_PATTERN}?$',
        videos.VideosView.as_view(), name='studio_content_videos'
    ),
    re_path(
        fr'^videos/images/{settings.COURSE_ID_PATTERN}$',
        videos.VideosView.as_view(), name='studio_content_videos'
    ),
    re_path(
        fr'^videos/encodings/{settings.COURSE_ID_PATTERN}$',
        videos.VideosView.as_view(), name='studio_content_videos'
    ),
    re_path(
        r'^videos/features/$',
        videos.VideosView.as_view(), name='studio_content_videos'
    ),
    re_path(
        fr'^videos/upload_link/{settings.COURSE_ID_PATTERN}$',
        videos.VideosView.as_view(), name='studio_content_videos'
    ),
]
