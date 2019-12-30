"""
Course Block API URLs
"""


from django.conf import settings
from django.conf.urls import url

from .views import BlocksInCourseView, BlocksView

urlpatterns = [
    # This endpoint requires the usage_key for the starting block.
    url(
        r'^v1/blocks/{}'.format(settings.USAGE_KEY_PATTERN),
        BlocksView.as_view(),
        kwargs={'hide_access_denials': True},
        name="blocks_in_block_tree"
    ),

    # This endpoint is an alternative to the above, but requires course_id as a parameter.
    url(
        r'^v1/blocks/',
        BlocksInCourseView.as_view(),
        kwargs={'hide_access_denials': True},
        name="blocks_in_course"
    ),
    # This endpoint requires the usage_key for the starting block.
    url(
        r'^v2/blocks/{}'.format(settings.USAGE_KEY_PATTERN),
        BlocksView.as_view(),
        name="blocks_in_block_tree"
    ),

    # This endpoint is an alternative to the above, but requires course_id as a parameter.
    url(
        r'^v2/blocks/',
        BlocksInCourseView.as_view(),
        name="blocks_in_course"
    ),
]
