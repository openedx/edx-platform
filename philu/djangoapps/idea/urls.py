from django.conf.urls import url

from philu.djangoapps.idea.views import (ChallengeLandingView, IdeaListingView, IdeaCreateView, IdeaDetailView)

urlpatterns = [
    url(
        r'^challenges/$',
        ChallengeLandingView.as_view(),
        name='challenge-landing'
    ),
    url(
        r'^ideas/$',
        IdeaListingView.as_view(),
        name='idea-listing'
    ),
    url(
        r'^ideas/create/$',
        IdeaCreateView.as_view(),
        name='idea-create'
    ),
    url(
        r'^ideas/(?P<pk>[0-9]+)/$',
        IdeaDetailView.as_view(),
        name='idea-details'
    ),
]
