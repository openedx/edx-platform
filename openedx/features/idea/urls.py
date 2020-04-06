from django.conf.urls import url

from openedx.features.idea.views import (ChallengeLandingView, IdeaListingView, IdeaCreateView, IdeaDetailView)

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
]
