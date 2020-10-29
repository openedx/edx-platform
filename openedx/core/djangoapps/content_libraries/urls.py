"""
URL configuration for Studio's Content Libraries REST API
"""
from __future__ import absolute_import, division, print_function, unicode_literals

from django.conf.urls import include, url

from . import views

# These URLs are only used in Studio. The LMS already provides all the
# API endpoints needed to serve XBlocks from content libraries using the
# standard XBlock REST API (see openedx.core.django_apps.xblock.rest_api.urls)
urlpatterns = [
    url(r'^api/libraries/v2/', include([
        # list of libraries / create a library:
        url(r'^$', views.LibraryRootView.as_view()),
        url(r'^(?P<lib_key_str>[^/]+)/', include([
            # get data about a library, update a library, or delete a library:
            url(r'^$', views.LibraryDetailsView.as_view()),
            # Get the list of XBlock types that can be added to this library
            url(r'^block_types/$', views.LibraryBlockTypesView.as_view()),
            # Get the list of XBlocks in this library, or add a new one:
            url(r'^blocks/$', views.LibraryBlocksView.as_view()),
            # Commit (POST) or revert (DELETE) all pending changes to this library:
            url(r'^commit/$', views.LibraryCommitView.as_view()),
        ])),
        url(r'^blocks/(?P<usage_key_str>[^/]+)/', include([
            # Get metadata about a specific XBlock in this library, or delete the block:
            url(r'^$', views.LibraryBlockView.as_view()),
            # Get the OLX source code of the specified block:
            url(r'^olx/$', views.LibraryBlockOlxView.as_view()),
            # TODO: Publish the draft changes made to this block:
            # url(r'^commit/$', views.LibraryBlockCommitView.as_view()),
            # View todo: discard draft changes
            # Future: set a block's tags (tags are stored in a Tag bundle and linked in)
        ])),
    ])),
]
