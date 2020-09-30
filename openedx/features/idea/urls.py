"""
Urls for idea app
"""
from django.conf.urls import url

from openedx.features.idea.api_views import FavoriteAPIView
from openedx.features.idea.views import ChallengeLandingView, IdeaCreateView, IdeaDetailView, IdeaListingView

urlpatterns = [
    url(
        r'^overview/$',
        ChallengeLandingView.as_view(),
        name='challenge-landing'
    ),
    url(
        r'^$',
        IdeaListingView.as_view(),
        name='idea-listing'
    ),
    url(
        r'^create/$',
        IdeaCreateView.as_view(),
        name='idea-create'
    ),
    url(
        r'^(?P<pk>[0-9]+)/$',
        IdeaDetailView.as_view(),
        name='idea-details'
    ),
    url(
        r'^api/favorite/(?P<idea_id>[0-9]+)/$',
        FavoriteAPIView.as_view(),
        name='mark-favorite-api-view'
    )
]
