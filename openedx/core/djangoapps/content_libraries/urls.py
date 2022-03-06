"""
URL configuration for Studio's Content Libraries REST API
"""

from django.urls import include, path, re_path

from rest_framework import routers

from . import views


# Django application name.

app_name = 'openedx.core.djangoapps.content_libraries'

# Router for importing blocks from courseware.

import_blocks_router = routers.DefaultRouter()
import_blocks_router.register(r'tasks', views.LibraryImportTaskViewSet, basename='import-block-task')

# These URLs are only used in Studio. The LMS already provides all the
# API endpoints needed to serve XBlocks from content libraries using the
# standard XBlock REST API (see openedx.core.django_apps.xblock.rest_api.urls)

urlpatterns = [
    path('api/libraries/v2/', include([
        # list of libraries / create a library:
        path('', views.LibraryRootView.as_view()),
        path('<str:lib_key_str>/', include([
            # get data about a library, update a library, or delete a library:
            path('', views.LibraryDetailsView.as_view()),
            # Get the list of XBlock types that can be added to this library
            path('block_types/', views.LibraryBlockTypesView.as_view()),
            # Get the list of Blockstore Bundle Links for this library, or add a new one:
            path('links/', views.LibraryLinksView.as_view()),
            # Update or delete a link:
            path('links/<str:link_id>/', views.LibraryLinkDetailView.as_view()),
            # Get the list of XBlocks in this library, or add a new one:
            path('blocks/', views.LibraryBlocksView.as_view()),
            # Commit (POST) or revert (DELETE) all pending changes to this library:
            path('commit/', views.LibraryCommitView.as_view()),
            # Get the list of users/groups who have permission to view/edit/administer this library:
            path('team/', views.LibraryTeamView.as_view()),
            # Add/Edit (PUT) or remove (DELETE) a user's permission to use this library
            path('team/user/<str:username>/', views.LibraryTeamUserView.as_view()),
            # Add/Edit (PUT) or remove (DELETE) a group's permission to use this library
            path('team/group/<str:group_name>/', views.LibraryTeamGroupView.as_view()),
            # Import blocks into this library.
            path('import_blocks/', include(import_blocks_router.urls)),
        ])),
        path('blocks/<str:usage_key_str>/', include([
            # Get metadata about a specific XBlock in this library, or delete the block:
            path('', views.LibraryBlockView.as_view()),
            # Get the LTI URL of a specific XBlock
            path('lti/', views.LibraryBlockLtiUrlView.as_view(), name='lti-url'),
            # Get the OLX source code of the specified block:
            path('olx/', views.LibraryBlockOlxView.as_view()),
            # CRUD for static asset files associated with a block in the library:
            path('assets/', views.LibraryBlockAssetListView.as_view()),
            path('assets/<path:file_path>', views.LibraryBlockAssetView.as_view()),
            # Future: publish/discard changes for just this one block
            # Future: set a block's tags (tags are stored in a Tag bundle and linked in)
        ])),
        re_path(r'^lti/1.3/', include([
            path('login/', views.LtiToolLoginView.as_view(), name='lti-login'),
            path('launch/', views.LtiToolLaunchView.as_view(), name='lti-launch'),
            path('pub/jwks/', views.LtiToolJwksView.as_view(), name='lti-pub-jwks'),
        ])),
    ])),
]
