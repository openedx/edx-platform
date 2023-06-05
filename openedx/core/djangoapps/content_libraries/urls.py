"""
URL configuration for Studio's Content Libraries REST API
"""
from django.conf.urls import include, url

from . import views


app_name = 'openedx.core.djangoapps.content_libraries'

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
            # Get the list of Blockstore Bundle Links for this library, or add a new one:
            url(r'^links/$', views.LibraryLinksView.as_view()),
            # Update or delete a link:
            url(r'^links/(?P<link_id>[^/]+)/$', views.LibraryLinkDetailView.as_view()),
            # Get the list of XBlocks in this library, or add a new one:
            url(r'^blocks/$', views.LibraryBlocksView.as_view()),
            # Commit (POST) or revert (DELETE) all pending changes to this library:
            url(r'^commit/$', views.LibraryCommitView.as_view()),
            # Get the list of users/groups who have permission to view/edit/administer this library:
            url(r'^team/$', views.LibraryTeamView.as_view()),
            # Add/Edit (PUT) or remove (DELETE) a user's permission to use this library
            url(r'^team/user/(?P<username>[^/]+)/$', views.LibraryTeamUserView.as_view()),
            # Add/Edit (PUT) or remove (DELETE) a group's permission to use this library
            url(r'^team/group/(?P<group_name>[^/]+)/$', views.LibraryTeamGroupView.as_view()),
        ])),
        url(r'^blocks/(?P<usage_key_str>[^/]+)/', include([
            # Get metadata about a specific XBlock in this library, or delete the block:
            url(r'^$', views.LibraryBlockView.as_view()),
            # Get the OLX source code of the specified block:
            url(r'^olx/$', views.LibraryBlockOlxView.as_view()),
            # CRUD for static asset files associated with a block in the library:
            url(r'^assets/$', views.LibraryBlockAssetListView.as_view()),
            url(r'^assets/(?P<file_path>.+)$', views.LibraryBlockAssetView.as_view()),
            # Future: publish/discard changes for just this one block
            # Future: set a block's tags (tags are stored in a Tag bundle and linked in)
        ])),
    ])),
]
