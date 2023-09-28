"""
Views for v1 contentstore API.
"""
from .course_details import CourseDetailsView
from .course_team import CourseTeamView
from .course_rerun import CourseRerunView
from .grading import CourseGradingView
from .proctoring import ProctoredExamSettingsView, ProctoringErrorsView
from .home import HomePageView
from .settings import CourseSettingsView
from .xblock import XblockView, XblockCreateView
from .assets import AssetsCreateRetrieveView, AssetsUpdateDestroyView
from .videos import (
    VideosUploadsView,
    VideosCreateUploadView,
    VideoImagesView,
    VideoEncodingsDownloadView,
    VideoFeaturesView
)
from .help_urls import HelpUrlsView
