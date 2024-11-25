"""Contenstore API v2 URLs."""

<<<<<<< HEAD
from django.urls import path

from cms.djangoapps.contentstore.rest_api.v2.views import HomePageCoursesViewV2

=======
from django.conf import settings
from django.urls import path, re_path

from cms.djangoapps.contentstore.rest_api.v2.views import home, downstreams
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
app_name = "v2"

urlpatterns = [
    path(
        "home/courses",
<<<<<<< HEAD
        HomePageCoursesViewV2.as_view(),
        name="courses",
    ),
=======
        home.HomePageCoursesViewV2.as_view(),
        name="courses",
    ),
    # TODO: Potential future path.
    # re_path(
    #     fr'^downstreams/$',
    #     downstreams.DownstreamsListView.as_view(),
    #     name="downstreams_list",
    # ),
    re_path(
        fr'^downstreams/{settings.USAGE_KEY_PATTERN}$',
        downstreams.DownstreamView.as_view(),
        name="downstream"
    ),
    re_path(
        fr'^downstreams/{settings.USAGE_KEY_PATTERN}/sync$',
        downstreams.SyncFromUpstreamView.as_view(),
        name="sync_from_upstream"
    ),
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
]
