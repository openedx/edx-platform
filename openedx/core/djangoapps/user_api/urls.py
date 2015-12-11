"""
Defines the URL routes for this app.
"""

from django.conf import settings
from django.conf.urls import patterns, url

from ..profile_images.views import ProfileImageView
from .accounts.views import AccountView
from .preferences.views import PreferencesView, PreferencesDetailView

urlpatterns = patterns(
    '',
    url(
        r'^v1/accounts/{}$'.format(settings.USERNAME_PATTERN),
        AccountView.as_view(),
        name="accounts_api"
    ),
    url(
        r'^v1/accounts/{}/image$'.format(settings.USERNAME_PATTERN),
        ProfileImageView.as_view(),
        name="accounts_profile_image_api"
    ),
    url(
        r'^v1/preferences/{}$'.format(settings.USERNAME_PATTERN),
        PreferencesView.as_view(),
        name="preferences_api"
    ),
    url(
        r'^v1/preferences/{}/(?P<preference_key>[a-zA-Z0-9_]+)$'.format(settings.USERNAME_PATTERN),
        PreferencesDetailView.as_view(),
        name="preferences_detail_api"
    ),
)
