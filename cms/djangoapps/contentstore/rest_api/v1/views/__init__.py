"""
Views for v1 contentstore API.
"""
from .certificates import CourseCertificatesView
from .course_details import CourseDetailsView
from .course_index import CourseIndexView
from .course_rerun import CourseRerunView
<<<<<<< HEAD
=======
from .course_waffle_flags import CourseWaffleFlagsView
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
from .course_team import CourseTeamView
from .grading import CourseGradingView
from .group_configurations import CourseGroupConfigurationsView
from .help_urls import HelpUrlsView
from .home import HomePageCoursesView, HomePageLibrariesView, HomePageView
from .proctoring import ProctoredExamSettingsView, ProctoringErrorsView
from .settings import CourseSettingsView
from .textbooks import CourseTextbooksView
from .vertical_block import ContainerHandlerView, VerticalContainerView
from .videos import (
    CourseVideosView,
    VideoDownloadView,
    VideoUsageView,
)
