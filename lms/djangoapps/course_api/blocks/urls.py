"""
Course Block API URLs
"""


from django.conf import settings
from django.conf.urls import url

from .views import BlocksInCourseView, BlocksView

urlpatterns = [
    # This endpoint requires the usage_key for the starting block.
    url(
        fr'^v1/blocks/{settings.USAGE_KEY_PATTERN}',
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
        fr'^v2/blocks/{settings.USAGE_KEY_PATTERN}',
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

if getattr(settings, 'PROVIDER_STATES_URL', None):
    from .tests.pacts.views import provider_state
    urlpatterns.append(url(
        r'^pact/provider_states/$',
        provider_state,
        name='provider-state-view'
    ))
